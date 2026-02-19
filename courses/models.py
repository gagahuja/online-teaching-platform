from django.db import models
from django.contrib.auth.models import User


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()

    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'is_staff': True}
    )

    price = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    is_free = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Module(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules'
    )
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

class ClassSession(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='sessions'
    )

    title = models.CharField(max_length=200)

    scheduled_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    meeting_room = models.CharField(max_length=255, blank=True, null=True)

    is_active = models.BooleanField(default=False)

    meeting_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.title} - {self.title}"

class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

class Enrollment(models.Model):
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )

    enrolled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} → {self.course.title}"


class Attendance(models.Model):
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE
    )

    session = models.ForeignKey(
        ClassSession,
        on_delete=models.CASCADE
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.session.title}"
