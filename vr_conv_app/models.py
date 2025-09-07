from django.db import models
from django.contrib.auth import get_user_model
from helper.models import UUIDPrimaryKey

User = get_user_model()

class Video(UUIDPrimaryKey):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="videos")
    original_file = models.FileField(upload_to="videos/originals/")
    filename = models.CharField(max_length=512, blank=True)
    thumbnail = models.ImageField(upload_to="videos/thumbnails/", null=True, blank=True)
    filesize = models.BigIntegerField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)  
    uploaded_at = models.DateTimeField(auto_now_add=True)

class ConversionJob(UUIDPrimaryKey):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("QUEUED", "Queued"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
        ("CANCELLED", "Cancelled"),
    ]

    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="jobs")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conversion_jobs")
    params = models.JSONField(default=dict, blank=True)  # e.g. {"method":"depth-warp", "layout":"side-by-side"}
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    progress = models.IntegerField(default=0)  # 0-100
    celery_task_id = models.CharField(max_length=255, blank=True, null=True)
    output_file = models.FileField(upload_to="videos/outputs/", null=True, blank=True)
    logs = models.TextField(blank=True)  # append logs/trace
    error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    
    class Meta:
        ordering = ["-created_at"]
    
