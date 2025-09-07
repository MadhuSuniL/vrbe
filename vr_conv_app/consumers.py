# consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class JobConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.job_id = self.scope["url_route"]["kwargs"]["job_id"]
        self.group_name = f"job_{self.job_id}"

        # Join job-specific group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave group when socket closes
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Called when Celery/background task sends updates
    async def job_update(self, event):
        # event is already a dict, just send as JSON
        await self.send_json({
            "status": event["status"].upper(),
            "progress": event.get("progress", 0),
            "output_file": event.get("output_file", ""),
        })

    # Optional: handle messages from client (if needed)
    async def receive_json(self, content, **kwargs):
        # For debugging or client-driven requests
        action = content.get("action")
        if action == "ping":
            await self.send_json({"message": "pong"})
