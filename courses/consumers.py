import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Attendance, ClassSession
from django.utils import timezone


class ClassroomConsumer(AsyncWebsocketConsumer):

    active_users = {}

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f"classroom_{self.session_id}"
        self.username = self.scope["user"].username

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        session = await ClassSession.objects.aget(id=self.session_id)

        await Attendance.objects.acreate(
            student=self.scope["user"],
            session=session
        )

        if self.room_group_name not in ClassroomConsumer.active_users:
            ClassroomConsumer.active_users[self.room_group_name] = []

        ClassroomConsumer.active_users[self.room_group_name].append(self.username)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "attendance_update",
                "users": ClassroomConsumer.active_users[self.room_group_name]
            }
        )

async def disconnect(self, close_code):

    from django.utils import timezone
    from courses.models import Attendance

    if self.room_group_name in ClassroomConsumer.active_users:
        if self.username in ClassroomConsumer.active_users[self.room_group_name]:
            ClassroomConsumer.active_users[self.room_group_name].remove(self.username)

    # update leave time
    try:
        attendance = Attendance.objects.filter(
            student__username=self.username,
            session_id=self.session_id
        ).last()

        if attendance and not attendance.leave_time:
            attendance.leave_time = timezone.now()
            attendance.save()

    except Exception as e:
        print("Attendance leave error:", e)

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