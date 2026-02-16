import os
from django.db.models.signals import post_migrate
from django.contrib.auth import get_user_model
from django.dispatch import receiver


@receiver(post_migrate)
def create_superuser(sender, **kwargs):
    username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

    if username and email and password:
        User = get_user_model()
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            print("Superuser created successfully")
