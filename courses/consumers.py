import json
from channels.generic.websocket import AsyncWebsocketConsumer


class ClassroomConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'classroom_{self.session_id}'
        self.username = self.scope["user"].username

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Notify others that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_join",
                "username": self.username
            }
        )

    async def disconnect(self, close_code):

        # Notify others that user left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_leave",
                "username": self.username
            }
        )

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "username": data["username"],
                "message": data["message"]
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat",
            "username": event["username"],
            "message": event["message"]
        }))

    async def user_join(self, event):
        await self.send(text_data=json.dumps({
            "type": "join",
            "username": event["username"]
        }))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps({
            "type": "leave",
            "username": event["username"]
        }))