from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from courses.models import Enrollment


def home(request):
    return render(request, "courses/home.html")


@login_required
def student_dashboard_v2(request):
    try:
        profile = request.user.studentprofile
        enrollments = Enrollment.objects.filter(student=profile)
    except:
        enrollments = []

    return render(request, "courses/student_dashboard_v2.html", {
        "enrollments": enrollments
    })


@login_required
def teacher_dashboard(request):
    return render(request, "courses/teacher_dashboard.html")


# SAFE PLACEHOLDER (so errors never happen)
def course_attendance(request, course_id):
    return render(request, "courses/home.html")