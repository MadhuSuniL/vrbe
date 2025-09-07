import subprocess
import json
import os
import tempfile
from django.core.files.base import ContentFile
from django.utils.timesince import timesince
from django.utils.timezone import now
from rest_framework import serializers
from . import models

class VideoSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = models.Video
        fields = "__all__"
        
    def get_time_ago(self, obj):
        if obj.uploaded_at:
            return f"{timesince(obj.uploaded_at, now())} ago"
        return None

    def create(self, validated_data):
        video = super().create(validated_data)
        file = validated_data.get("original_file")

        if file:
            # Filename & filesize
            video.filename = os.path.basename(file.name)
            video.filesize = file.size

            # Duration via ffprobe
            try:
                cmd = [
                    "ffprobe", "-v", "error", "-show_entries",
                    "format=duration", "-of", "json",
                    file.temporary_file_path()
                ]
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                data = json.loads(result.stdout)
                video.duration = float(data["format"]["duration"])
            except Exception:
                video.duration = None

            # Thumbnail via ffmpeg
            try:
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_thumb:
                    tmp_thumb_path = tmp_thumb.name

                cmd = [
                    "ffmpeg", "-i", file.temporary_file_path(),
                    "-ss", "00:00:01", "-vframes", "1", tmp_thumb_path, "-y"
                ]
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

                with open(tmp_thumb_path, "rb") as f:
                    video.thumbnail.save(f"{video.filename}_thumb.jpg", ContentFile(f.read()), save=False)

                os.remove(tmp_thumb_path)
            except Exception:
                video.thumbnail = None

            video.save(update_fields=["filename", "filesize", "duration", "thumbnail"])

        return video


class ConversionJobSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default = serializers.CurrentUserDefault())
    video_details = serializers.SerializerMethodField(read_only=True)
    
    def get_video_details(self, obj):
        if obj.video:
            return VideoSerializer(obj.video, context = self.context).data
        return None
    
    def create(self, validated_data):
        print(validated_data)
        job : models.ConversionJob = super().create(validated_data)
        from .tasks import process_video
        process_video.delay(job.id) 
        return job
    
    class Meta:
        model = models.ConversionJob
        fields = "__all__"



    
        
        
        