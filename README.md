# 🎥 VR Backend (vrbe)

This is the **Django backend** for the VR Video Conversion project.  
It supports **video uploads, VR180 stereo conversion, WebSocket progress updates, and Celery background processing**.  

---

## ⚡ Features
- ✅ User authentication (JWT)  
- ✅ Video upload & conversion jobs  
- ✅ VR180 video conversion (depth estimation + stereo synthesis)  
- ✅ Audio track preservation  
- ✅ Metadata injection for VR compatibility (YouTube VR)  
- ✅ Real-time progress updates via **Django Channels & WebSockets**  
- ✅ Task management with **Celery + Redis**  

---

## 📦 Requirements

- Python 3.10+  
- Django 5.x  
- Redis (for Celery + Channels backend)  
- FFmpeg (for audio/video processing)  
- Node.js (optional, for frontend)  

---

## 🔧 Installation

Clone the repository:

```bash
git clone https://github.com/MadhuSuniL/vrbe.git
cd vrbe
````

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration

### Django Channels

We use **ASGI** with Channels for WebSocket support.
Install with:

```bash
python -m pip install -U "channels[daphne]"
```

And in `settings.py`:

```python
ASGI_APPLICATION = "vrbe.asgi.application"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
```

### Celery + Redis

Celery is used for background video processing.

Start a Redis server (Linux/macOS):

```bash
redis-server
```

Start Celery worker:

```bash
celery -A config worker -l info -P eventlet
```

---

## ▶️ Running the Project

Start Django (with ASGI server):

```bash
python manage.py runserver
```

Run Celery worker (in another terminal):

```bash
celery -A config worker -l info -P eventlet
```

Now your backend is ready 🚀

---

## 🔌 WebSocket API

WebSocket Endpoint:

```
ws://127.0.0.1:8000/ws/jobs/<job_id>/
```

Example message from server:

```json
{
  "status": "PROCESSING",
  "progress": 40
}
```

---

## 🎬 Video Conversion Pipeline

1. User uploads a video.
2. A Celery task starts processing:

   * Depth estimation (MiDaS model, PyTorch)
   * Stereo synthesis for VR180
   * Audio merging
   * Metadata injection (YouTube VR support)
3. WebSocket updates progress in real-time.
4. Final VR180 video stored in `media/videos/outputs/`.

---

## 📄 API Documentation

📌 REST API docs (sample link for now):
👉 [API Docs](https://documenter.getpostman.com/view/38405494/2sB3Hkr1iP)

---

## 🚀 Deployment Notes

* Use **Daphne** instead of Gunicorn for ASGI:

  ```bash
  daphne -b 0.0.0.0 -p 8000 vrbe.asgi:application
  ```
* Use **NGINX** to serve media files.
* Configure Celery with **systemd** for production stability.

---

## 👨‍💻 Author

Developed by **Madhu SuniL** ✨
Backend repo: [vrbe](https://github.com/MadhuSuniL/vrbe)
