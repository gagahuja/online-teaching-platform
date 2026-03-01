from sys import modules

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from courses.models import Course, ClassSession, StudentProfile, Enrollment, Attendance
from django.utils.timezone import localtime
from datetime import datetime
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from courses.models import Module, ModuleProgress
from reportlab.pdfgen import canvas
from django.shortcuts import render, redirect

import json


@login_required
def live_class(request, session_id):

    session = get_object_or_404(ClassSession, id=session_id)
    user = request.user

    profile = StudentProfile.objects.get(user=user)

    # Permission check
    if profile.role == "student":
        enrolled = Enrollment.objects.filter(
            student=profile,
            course=session.course
        ).exists()

        if not enrolled:
            return HttpResponseForbidden("Not enrolled")

    # Attendance auto log
    if profile.role == "student":
        Attendance.objects.get_or_create(
            student=profile,
            session=session
        )

    meeting_name = f"ScoreSkill_{session.course.id}_{session.id}"

    return render(request, "courses/live_class.html", {
        "session": session,
        "meeting_name": meeting_name,
        "user_role": profile.role
    })

@login_required
def home(request):

    profile = StudentProfile.objects.get(user=request.user)

    if profile.role == "teacher":
        return teacher_dashboard(request)

    enrollments = profile.enrollment_set.select_related("course")

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

@require_POST
@login_required
def toggle_session(request, session_id):
    if not request.user.is_staff:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    session = ClassSession.objects.get(id=session_id)

    action = request.POST.get("action")

    if action == "start":
        session.is_active = True
    elif action == "end":
        session.is_active = False
    else:
        return JsonResponse({"error": "Invalid action"}, status=400)

    session.save()

    return JsonResponse({
        "success": True,
        "is_active": session.is_active
    })

@login_required
def course_attendance(request, course_id):
    if not request.user.is_staff:
        return HttpResponseForbidden("Unauthorized")

    course = Course.objects.get(id=course_id)

    sessions_data = []

    for session in course.classsession_set.all():
        attendance_records = Attendance.objects.filter(session=session)

        records = []
        for record in attendance_records:
            records.append({
                "student": record.student.user.username,
                "joined_at": record.joined_at
            })

        sessions_data.append({
            "session_title": session.title,
            "scheduled_date": session.scheduled_date,
            "records": records
        })

    context = {
        "course": course,
        "sessions_data": sessions_data
    }

    return render(request, "courses/attendance.html", context)

@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Ensure profile exists
    student, created = StudentProfile.objects.get_or_create(user=request.user)

    # Only students can enroll
    if student.role != 'student':
        return redirect('home')

    Enrollment.objects.get_or_create(student=student, course=course)

    return redirect('home')


from django.utils import timezone



@require_POST
@login_required
def toggle_module_completion(request, module_id):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    module = get_object_or_404(Module, id=module_id)

    progress, created = ModuleProgress.objects.get_or_create(
        student=profile,
        module=module
    )

    progress.completed = not progress.completed
    progress.save()

    # Recalculate progress %
    total_modules = module.course.modules.count()
    completed_count = ModuleProgress.objects.filter(
        student=profile,
        module__course=module.course,
        completed=True
    ).count()

    percent = 0
    if total_modules > 0:
        percent = int((completed_count / total_modules) * 100)

    return JsonResponse({
        "completed": progress.completed,
        "progress_percent": percent
    })


from django.shortcuts import render, get_object_or_404
from courses.models import Course, Module, ModuleProgress, ClassSession, StudentProfile
from django.contrib.auth.decorators import login_required


@login_required
def course_detail(request, course_id):

    course = get_object_or_404(Course, id=course_id)

    profile = StudentProfile.objects.get(user=request.user)

    modules = Module.objects.filter(course=course).order_by("order")

    module_data = []

    previous_completed = True

    for module in modules:

        completed = ModuleProgress.objects.filter(
            student=profile,
            module=module,
            completed=True
        ).exists()

        locked = not previous_completed

        module_data.append({
            "id": module.id,
            "title": module.title,
            "order": module.order,
            "completed": completed,
            "locked": locked
        })

        previous_completed = completed


    completed_count = ModuleProgress.objects.filter(
        student=profile,
        module__course=course,
        completed=True
    ).count()

    total_modules = modules.count()

    progress_percent = 0

    if total_modules > 0:
        progress_percent = int((completed_count / total_modules) * 100)


    sessions = ClassSession.objects.filter(course=course)


    return render(request, "courses/course_detail.html", {
        "course": course,
        "modules": module_data,
        "sessions": sessions,
        "progress_percent": progress_percent
    })


@login_required
def download_certificate(request, course_id):

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    from datetime import datetime

    course = get_object_or_404(Course, id=course_id)
    profile = StudentProfile.objects.get(user=request.user)

    total_modules = Module.objects.filter(course=course).count()

    completed_modules = ModuleProgress.objects.filter(
        student=profile,
        module__course=course,
        completed=True
    ).count()

    if total_modules == 0 or completed_modules < total_modules:
        return HttpResponse("Course not completed", status=403)


    response = HttpResponse(content_type='application/pdf')

    response['Content-Disposition'] = (
        f'attachment; filename="ScoreSkill_Certificate_{course.title}.pdf"'
    )

    p = canvas.Canvas(response, pagesize=A4)

    width, height = A4


    # Border
    p.setLineWidth(4)
    p.rect(30, 30, width - 60, height - 60)


    # Title
    p.setFont("Helvetica-Bold", 32)
    p.drawCentredString(width / 2, height - 150, "Certificate of Completion")


    # Subtitle
    p.setFont("Helvetica", 18)
    p.drawCentredString(width / 2, height - 220, "This certifies that")


    # Student Name
    p.setFont("Helvetica-Bold", 24)
    p.drawCentredString(width / 2, height - 280, request.user.username)


    # Course text
    p.setFont("Helvetica", 18)
    p.drawCentredString(width / 2, height - 340, "has successfully completed the course")


    # Course Name
    p.setFont("Helvetica-Bold", 22)
    p.drawCentredString(width / 2, height - 400, course.title)


    # Date
    date = datetime.now().strftime("%d %B %Y")

    p.setFont("Helvetica", 14)
    p.drawCentredString(width / 2, height - 480, f"Date: {date}")


    # Footer
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, height - 550, "Score Skill LMS")


    p.save()

    return response

    # ===============================
# TEACHER DASHBOARD
# ===============================

from django.contrib.auth.decorators import login_required
from courses.models import Course, ClassSession, StudentProfile
from django.shortcuts import render

@login_required
def teacher_dashboard(request):

    profile = StudentProfile.objects.get(user=request.user)

    if profile.role != "teacher":
        return render(request, "courses/home.html")

    courses = Course.objects.filter(teacher=request.user)

    course_sessions = []

    for course in courses:
        sessions = ClassSession.objects.filter(course=course).order_by("scheduled_date")

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

    profile = StudentProfile.objects.get(user=request.user)

    if profile.role != "teacher":
        return redirect("home")

    if request.method == "POST":

        title = request.POST.get("title")

        description = request.POST.get("description")

        price = request.POST.get("price") or 0

        Course.objects.create(
            title=title,
            description=description,
            teacher=request.user,
            price=price
        )

        return redirect("teacher_dashboard")

    return render(request, "courses/create_course.html")


# ===============================
# ADD MODULE
# ===============================

@login_required
def add_module(request, course_id):

    course = Course.objects.get(id=course_id)

    if request.method == "POST":

        title = request.POST.get("title")

        order = request.POST.get("order")

        Module.objects.create(
            course=course,
            title=title,
            order=order
        )

        return redirect("teacher_dashboard")

    return render(
        request,
        "courses/add_module.html",
        {"course": course}
    )


# ===============================
# ADD SESSION
# ===============================

@login_required
def add_session(request, course_id):

    course = Course.objects.get(id=course_id)

    if request.method == "POST":

        title = request.POST.get("title")

        date = request.POST.get("date")

        start = request.POST.get("start")

        end = request.POST.get("end")

        ClassSession.objects.create(
            course=course,
            title=title,
            scheduled_date=date,
            start_time=start,
            end_time=end
        )

        return redirect("teacher_dashboard")

    return render(
        request,
        "courses/add_session.html",
        {"course": course}
    )


    from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from courses.models import Course, StudentProfile

@login_required
def create_course(request):
    
    profile = StudentProfile.objects.get(user=request.user)

    # Only teacher allowed
    if profile.role != "teacher":
        return redirect("home")

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        price = request.POST.get("price") or 0
        is_free = request.POST.get("is_free") == "on"

        Course.objects.create(
            title=title,
            description=description,
            teacher=request.user,
            price=price,
            is_free=is_free
        )

        return redirect("teacher_dashboard")

    return render(request, "courses/create_course.html")

from courses.forms import CourseForm
from django.contrib.auth.decorators import login_required

@login_required
def create_course(request):

    profile = request.user.studentprofile

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

    return render(request, "courses/create_course.html", {
        "form": form
    })



from courses.forms import ModuleForm

@login_required
def add_module(request, course_id):

    profile = request.user.studentprofile

    if profile.role != "teacher":
        return redirect("home")

    course = Course.objects.get(id=course_id)

    if request.method == "POST":

        form = ModuleForm(request.POST)

        if form.is_valid():

            module = form.save(commit=False)

            module.course = course

            module.save()

            return redirect("teacher_dashboard")

    else:

        form = ModuleForm()

    return render(request, "courses/add_module.html", {
        "form": form,
        "course": course
    })


@login_required
def manage_course(request, course_id):

    profile = request.user.studentprofile

    if profile.role != "teacher":
        return redirect("home")

    course = Course.objects.get(id=course_id)

    modules = course.modules.all()

    return render(request, "courses/manage_course.html", {
        "course": course,
        "modules": modules
    })


from courses.forms import SessionForm

@login_required
def add_session(request, course_id):

    profile = request.user.studentprofile

    if profile.role != "teacher":
        return redirect("home")

    course = Course.objects.get(id=course_id)

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


@login_required
def student_dashboard(request):

    profile = request.user.studentprofile

    if profile.role != 'student':
        return redirect('home')

    enrollments = Enrollment.objects.filter(student=profile)

    context = {
        "enrollments": enrollments
    }

    return render(request, "courses/student_dashboard.html", context)



@login_required
def teacher_live_panel(request, session_id):

    profile = StudentProfile.objects.get(user=request.user)

    if profile.role != "teacher":
        return HttpResponseForbidden()

    session = ClassSession.objects.get(id=session_id)

    attendance = Attendance.objects.filter(session=session)

    return render(request, "courses/teacher_live_panel.html", {
        "session": session,
        "attendance": attendance
    })


@login_required
def toggle_session_status(request, session_id):

    if request.method == "POST":

        session = ClassSession.objects.get(id=session_id)

        data = json.loads(request.body)

        action = data.get("action")

        if action == "start":
            session.is_active = True

        elif action == "end":
            session.is_active = False

        session.save()

        return JsonResponse({"success": True})

    return JsonResponse({"success": False})



from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@login_required
def start_session(request, session_id):
    if request.method == "POST":
        session = ClassSession.objects.get(id=session_id)
        session.is_active = True
        session.save()

        return JsonResponse({
            "success": True,
            "status": "started"
        })

    return JsonResponse({"success": False})


@csrf_exempt
@login_required
def stop_session(request, session_id):
    if request.method == "POST":
        session = ClassSession.objects.get(id=session_id)
        session.is_active = False
        session.save()

        return JsonResponse({
            "success": True,
            "status": "stopped"
        })

    return JsonResponse({"success": False})