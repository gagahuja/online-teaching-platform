import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Attendance, ClassSession
from django.utils import timezone


class ClassroomConsumer(AsyncWebsocketConsumer):

    active_users = {}  # {room: {username: join_time}}

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f"classroom_{self.session_id}"
        self.username = self.scope["user"].username

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        

        if self.room_group_name not in ClassroomConsumer.active_users:
            ClassroomConsumer.active_users[self.room_group_name] = {}

            ClassroomConsumer.active_users[self.room_group_name][self.username] = timezone.now().strftime("%H:%M:%S")

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "attendance_update",
                "users": [
                    {
                        "username": username,
                        "join_time": join_time
                    }
                    for username, join_time in ClassroomConsumer.active_users[self.room_group_name].items()
                ]
            }
        )

        

from asgiref.sync import sync_to_async

async def disconnect(self, close_code):

    if self.room_group_name in ClassroomConsumer.active_users:
        ClassroomConsumer.active_users[self.room_group_name].pop(self.username, None)

    # ✅ SAFE DB UPDATE
    @sync_to_async
    def update_leave():
        attendance = Attendance.objects.filter(
            student__username=self.username,
            session_id=self.session_id,
            leave_time__isnull=True
        ).last()

        if attendance:
            attendance.leave_time = timezone.now()
            attendance.save()

    try:
        await update_leave()
    except Exception as e:
        print("Leave error:", e)

    await self.channel_layer.group_send(
        self.room_group_name,
        {
            "type": "attendance_update",
            "users": [
                {
                    "username": username,
                    "join_time": join_time
                }
                for username, join_time in ClassroomConsumer.active_users.get(self.room_group_name, {}).items()
            ]
        }
    )

    await self.channel_layer.group_discard(
        self.room_group_name,
        self.channel_name
    )

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data["type"] == "chat":

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "username": data["username"],
                    "message": data["message"]
                }
            )

        elif data["type"] == "raise_hand":

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "hand_raised",
                    "username": data["username"]
                }
            )

        elif data["type"] == "remove_student":

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "student_removed",
                    "username": data["username"]
                }
            )

        elif data["type"] == "end_class":

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "class_ended"
                }
            )

    async def chat_message(self, event):

        await self.send(text_data=json.dumps({
            "type": "chat",
            "username": event["username"],
            "message": event["message"]
        }))

    async def hand_raised(self, event):

        await self.send(text_data=json.dumps({
            "type": "hand",
            "username": event["username"]
        }))

    async def student_removed(self, event):

        if self.username == event["username"]:

            await self.send(text_data=json.dumps({
                "type": "removed"
            }))

    async def attendance_update(self, event):

        await self.send(text_data=json.dumps({
            "type": "attendance",
            "users": event["users"]
        }))

    async def class_ended(self, event):

        await self.send(text_data=json.dumps({
            "type": "class_end"
        }))