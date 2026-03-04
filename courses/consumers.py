import json
from channels.generic.websocket import AsyncWebsocketConsumer


class ClassroomConsumer(AsyncWebsocketConsumer):

    # store active users per room
    active_users = {}

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'classroom_{self.session_id}'
        self.username = self.scope["user"].username

        # join group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # add user to active list
        if self.room_group_name not in ClassroomConsumer.active_users:
            ClassroomConsumer.active_users[self.room_group_name] = []

        ClassroomConsumer.active_users[self.room_group_name].append(self.username)

        # broadcast updated user list
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "attendance_update",
                "users": ClassroomConsumer.active_users[self.room_group_name]
            }
        )

    async def disconnect(self, close_code):

        # remove user
        if self.room_group_name in ClassroomConsumer.active_users:
            if self.username in ClassroomConsumer.active_users[self.room_group_name]:
                ClassroomConsumer.active_users[self.room_group_name].remove(self.username)

        # broadcast updated list
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "attendance_update",
                "users": ClassroomConsumer.active_users.get(self.room_group_name, [])
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

    async def attendance_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "attendance",
            "users": event["users"]
        }))