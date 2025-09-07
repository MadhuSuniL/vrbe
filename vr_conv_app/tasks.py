import json
import torch
import cv2
import numpy as np
from tqdm import tqdm
import subprocess
import os
from celery import shared_task
from django.conf import settings
from .models import ConversionJob
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_progress(job_id, progress, status, output_file_url=None):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"job_{job_id}",
        {
            "type": "job_update",
            "progress": progress,
            "status": status,
            "output_file": output_file_url,
        },
    )


def has_audio(file_path: str) -> bool:
    """Check if a video has an audio stream using ffprobe."""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a",
            "-show_entries", "stream=codec_type",
            "-of", "json",
            file_path,
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        info = json.loads(result.stdout)
        return "streams" in info and len(info["streams"]) > 0
    except Exception:
        return False


@shared_task(bind=True)
def process_video(self, job_id):
    try:
        job: ConversionJob = ConversionJob.objects.get(id=job_id)
        job.status = "PROCESSING"
        job.save(update_fields=["status"])

        # 🔔 Notify start
        send_progress(job.id, 0, "PROCESSING")

        input_path = job.video.original_file.path
        base_name = os.path.splitext(os.path.basename(input_path))[0]

        # ===== DEPTH MODEL LOADING =====
        midas = torch.hub.load("intel-isl/MiDaS", "DPT_Hybrid")
        midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
        transform = midas_transforms.small_transform
        midas.eval()

        # ===== VIDEO PROCESSING =====
        cap = cv2.VideoCapture(input_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        temp_output = os.path.join(settings.MEDIA_ROOT, f"{base_name}_lr.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_output, fourcc, fps, (w * 2, h))

        for idx in tqdm(range(total_frames), desc="Processing frames"):
            ret, frame = cap.read()
            if not ret:
                break

            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Depth inference
            input_batch = transform(img).to("cpu")
            with torch.no_grad():
                depth = midas(input_batch).squeeze().cpu().numpy()

            depth = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8)
            depth_resized = cv2.resize(depth, (w, h))

            # Right-eye synthesis
            max_shift = 20
            right = np.zeros_like(frame)
            for y in range(h):
                shift_row = np.roll(
                    frame[y, :, :],
                    int((1 - depth_resized[y, 0]) * max_shift),
                    axis=0,
                )
                right[y, :, :] = shift_row

            stereo = np.concatenate((frame, right), axis=1)
            out.write(stereo)

            # 🔔 Progress updates
            progress = int((idx + 1) / total_frames * 100)
            if progress % 5 == 0:
                send_progress(job.id, progress, "PROCESSING")

        cap.release()
        out.release()

        # ===== STEP 1: AUDIO FIX =====
        final_temp = os.path.join(settings.MEDIA_ROOT, f"videos/outputs/{base_name}_merged.mp4")
        if has_audio(input_path):
            cmd_audio = (
                f'ffmpeg -y -i "{temp_output}" -i "{input_path}" '
                f'-c:v copy -c:a aac -strict -2 -map 0:v:0 -map 1:a:0 "{final_temp}"'
            )
        else:
            cmd_audio = f'ffmpeg -y -i "{temp_output}" -c:v copy "{final_temp}"'
        subprocess.run(cmd_audio, shell=True, check=True)

        # ===== STEP 2: VR180 METADATA INJECTION (FINAL STEP) =====
        final_output = os.path.join(settings.MEDIA_ROOT, f"videos/outputs/{base_name}_vr180.mp4")
        cmd_meta = (
            f"python spatial-media/spatialmedia -i "
            f"--stereo=left-right --projection=equirectangular "
            f"\"{final_temp}\" \"{final_output}\""
        )
        subprocess.run(cmd_meta, shell=True, check=True)

        # Save result
        job.output_file.name = f"videos/outputs/{base_name}_vr180.mp4"
        job.status = "COMPLETED"
        job.save(update_fields=["output_file", "status"])

        # 🔔 Final completion
        send_progress(job.id, 100, "COMPLETED", job.output_file.url)

        return {"job_id": str(job.id), "status": "COMPLETED", "output_file": job.output_file.url}

    except Exception as e:
        job = ConversionJob.objects.get(id=job_id)
        job.status = "FAILED"
        job.error = str(e)
        job.save(update_fields=["status", "error"])

        # 🔔 Notify failure
        send_progress(job.id, 0, "FAILED")

        raise
