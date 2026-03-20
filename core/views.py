from django.shortcuts import render
from django.http import HttpResponse


def home(request):
    return HttpResponse("Website is working ✅")


def student_dashboard_v2(request):
    return HttpResponse("Student Dashboard Working ✅")


def teacher_dashboard(request):
    return HttpResponse("Teacher Dashboard Working ✅")


def course_attendance(request, course_id):
    return HttpResponse("Attendance Page ✅")