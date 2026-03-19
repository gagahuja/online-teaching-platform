from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from courses.models import (
    Course, ClassSession, StudentProfile,
    Enrollment, Attendance, Module, ModuleProgress
)

from courses.forms import CourseForm, ModuleForm, SessionForm

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
import json


# ===============================
# HOME
# ===============================
@login_required
def home(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if profile.role == "teacher":
        return teacher_dashboard(request)

    enrollments = Enrollment.objects.filter(student=profile)

    course_sessions = []
    for enrollment in enrollments:
        sessions = ClassSession.objects.filter(
            course=enrollment.course,
            is_active=True
        )

        course_sessions.append({
            "course": enrollment.course,
            "sessions": sessions
        })

    return render(request, "courses/home.html", {
        "course_sessions": course_sessions
    })


# ===============================
# STUDENT DASHBOARD
# ===============================
@login_required
def student_dashboard_v2(request):
    profile, created = StudentProfile.objects.get_or_create(user=request.user)

    # 🔥 FIX: ensure role always exists
    if not profile.role:
        profile.role = "student"
        profile.save()

    if profile.role != 'student':
        return redirect('home')

    enrollments = Enrollment.objects.filter(student=profile)

    return render(request, "courses/student_dashboard_v2.html", {
        "enrollments": enrollments
    })


# ===============================
# ENROLL COURSE
# ===============================
@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if profile.role != 'student':
        return redirect('home')

    Enrollment.objects.get_or_create(student=profile, course=course)

    return redirect('home')


# ===============================
# TEACHER DASHBOARD
# ===============================
@login_required
def teacher_dashboard(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if profile.role != "teacher":
        return redirect("home")

    courses = Course.objects.filter(teacher=request.user)

    course_sessions = []
    for course in courses:
        sessions = ClassSession.objects.filter(course=course)

        course_sessions.append({
            "course": course,
            "sessions": sessions
        })

    return render(request, "courses/teacher_dashboard.html", {
        "course_sessions": course_sessions
    })


# ===============================
# CREATE COURSE
# ===============================
@login_required
def create_course(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if profile.role != "teacher":
        return redirect("home")

    if request.method == "POST":
        form = CourseForm(request.POST)

        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            return redirect("teacher_dashboard")
    else:
        form = CourseForm()

    return render(request, "courses/create_course.html", {"form": form})


# ===============================
# ADD MODULE
# ===============================
@login_required
def add_module(request, course_id):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if profile.role != "teacher":
        return redirect("home")

    course = get_object_or_404(Course, id=course_id)

    if request.method == "POST":
        form = ModuleForm(request.POST)

        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.save()
            return redirect("manage_course", course_id=course.id)
    else:
        form = ModuleForm()

    return render(request, "courses/add_module.html", {
        "form": form,
        "course": course
    })


# ===============================
# ADD SESSION
# ===============================
@login_required
def add_session(request, course_id):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if profile.role != "teacher":
        return redirect("home")

    course = get_object_or_404(Course, id=course_id)

    if request.method == "POST":
        form = SessionForm(request.POST)

        if form.is_valid():
            session = form.save(commit=False)
            session.course = course
            session.save()
            return redirect("manage_course", course_id=course.id)
    else:
        form = SessionForm()

    return render(request, "courses/add_session.html", {
        "form": form,
        "course": course
    })


# ===============================
# MANAGE COURSE
# ===============================
@login_required
def manage_course(request, course_id):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if profile.role != "teacher":
        return redirect("home")

    course = get_object_or_404(Course, id=course_id)

    return render(request, "courses/manage_course.html", {
        "course": course,
        "modules": course.modules.all()
    })


# ===============================
# COURSE DETAIL + PROGRESS
# ===============================
@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    modules = course.modules.all()

    completed = ModuleProgress.objects.filter(
        student=profile,
        module__course=course,
        completed=True
    ).count()

    total = modules.count()

    progress_percent = int((completed / total) * 100) if total else 0

    sessions = ClassSession.objects.filter(course=course)

    return render(request, "courses/course_detail.html", {
        "course": course,
        "modules": modules,
        "sessions": sessions,
        "progress_percent": progress_percent
    })


# ===============================
# MODULE TOGGLE
# ===============================
@require_POST
@login_required
def toggle_module_completion(request, module_id):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    module = get_object_or_404(Module, id=module_id)

    progress, _ = ModuleProgress.objects.get_or_create(
        student=profile,
        module=module
    )

    progress.completed = not progress.completed
    progress.save()

    return JsonResponse({"completed": progress.completed})


# ===============================
# START / STOP SESSION
# ===============================
@csrf_exempt
@login_required
def start_session(request, session_id):
    session = get_object_or_404(ClassSession, id=session_id)
    session.is_active = True
    session.save()
    return JsonResponse({"success": True})


@csrf_exempt
@login_required
def stop_session(request, session_id):
    session = get_object_or_404(ClassSession, id=session_id)
    session.is_active = False
    session.save()
    return JsonResponse({"success": True})


# ===============================
# ATTENDANCE REPORT
# ===============================
@login_required
def attendance_report(request, session_id):
    session = get_object_or_404(ClassSession, id=session_id)

    records = Attendance.objects.filter(session=session)

    return render(request, "courses/attendance.html", {
        "session": session,
        "records": records
    })


# ===============================
# CERTIFICATE
# ===============================
@login_required
def download_certificate(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    total = course.modules.count()
    completed = ModuleProgress.objects.filter(
        student=profile,
        module__course=course,
        completed=True
    ).count()

    if completed < total:
        return HttpResponse("Complete course first", status=403)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{course.title}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)

    p.drawString(200, 750, "Certificate of Completion")
    p.drawString(200, 700, request.user.username)
    p.drawString(200, 650, course.title)

    p.save()

    return response