from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from courses.models import Enrollment


def home(request):
    if request.user.is_authenticated:
        try:
            profile = request.user.studentprofile

            if profile.role == "teacher":
                return redirect("teacher_dashboard")
            else:
                return redirect("student_dashboard")

        except:
            return redirect("student_dashboard")

    return render(request, "courses/home.html")


@login_required
def student_dashboard_v2(request):
    enrollments = Enrollment.objects.filter(student=request.user.studentprofile)

    return render(request, "courses/student_dashboard_v2.html", {
        "enrollments": enrollments
    })


@login_required
def teacher_dashboard(request):
    return render(request, "courses/teacher_dashboard.html")


# SAFE PLACEHOLDER (so errors never happen)
def course_attendance(request, course_id):
    return render(request, "courses/home.html")