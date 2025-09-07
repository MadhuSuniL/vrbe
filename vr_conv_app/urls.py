from django.urls import path, re_path
from . import views, consumers

urlpatterns = [
    path("upload-video/", views.UploadVideoView.as_view(), name="upload-video"),
    path("job/<pk>", views.ConversationJobRetrievetView.as_view(), name="job-retrieve"),
    path("jobs/", views.ConversationJobListView.as_view(), name="job-list"),
    path("jobs/create/", views.ConversationJobCreateView.as_view(), name="job-create"),
]


websocket_urlpatterns = [
    re_path(r"^ws/jobs/(?P<job_id>[0-9a-f-]+)/$", consumers.JobConsumer.as_asgi()),
]