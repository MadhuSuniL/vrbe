from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from . import serializers, models


class UploadVideoView(CreateAPIView):
    serializer_class = serializers.VideoSerializer
    queryset = models.Video.objects.all()
    

class ConversationJobRetrievetView(RetrieveAPIView):
    serializer_class = serializers.ConversionJobSerializer
    queryset = models.ConversionJob.objects.all()
    
    def get_queryset(self):
        return self.queryset.filter(owner = self.request.user)


class ConversationJobListView(ListAPIView):
    serializer_class = serializers.ConversionJobSerializer
    queryset = models.ConversionJob.objects.all()
    
    def get_queryset(self):
        return self.queryset.filter(owner = self.request.user)


class ConversationJobCreateView(CreateAPIView):
    serializer_class = serializers.ConversionJobSerializer
    queryset = models.ConversionJob.objects.all()
