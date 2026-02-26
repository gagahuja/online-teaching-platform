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




@login_required
def live_class(request, session_id):
    session = get_object_or_404(ClassSession, id=session_id)
    user = request.user

    # Permission check
    if user.is_staff:
        allowed = True
    else:
        try:
            student = StudentProfile.objects.get(user=user)
            allowed = Enrollment.objects.filter(
                student=student,
                course=session.course
            ).exists()
        except StudentProfile.DoesNotExist:
            allowed = False

    if not allowed:
        return HttpResponseForbidden("You are not enrolled in this course.")

    # 🕒 Time restriction
    now = localtime()

    session_start = datetime.combine(
        session.scheduled_date,
        session.start_time
    )

    session_end = datetime.combine(
        session.scheduled_date,
        session.end_time
    )

    if now.replace(tzinfo=None) < session_start:
        return HttpResponseForbidden("Class has not started yet.")

    if now.replace(tzinfo=None) > session_end:
        return HttpResponseForbidden("Class has already ended.")
    
    if not session.is_active:
        return HttpResponseForbidden("Class has not been started by the teacher yet.")


    # Attendance
    if not user.is_staff:
        student = StudentProfile.objects.get(user=user)

        Attendance.objects.get_or_create(
            student=student,
            session=session
        )

    meeting_name = f"course{session.course.id}_session{session.id}"

    return render(request, 'courses/live_class.html', {
        'session': session,
        'meeting_name': meeting_name,
    })

from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render





@login_required
def home(request):
    user = request.user
    profile, _ = StudentProfile.objects.get_or_create(user=user)

    all_courses = Course.objects.all()
    now = localtime().replace(tzinfo=None)

    if profile.role == "student":

        enrolled_courses = Course.objects.filter(
            enrollment__student=profile
        ).distinct()

        available_courses = all_courses.exclude(
            enrollment__student=profile
        )

        enrolled_data = []

        for course in enrolled_courses:
            sessions = course.sessions.all()

            next_status = "no_sessions"
            next_session = None

            for session in sessions:
                session_start = datetime.combine(
                    session.scheduled_date,
                    session.start_time
                )
                session_end = datetime.combine(
                    session.scheduled_date,
                    session.end_time
                )

                if session_start <= now <= session_end and session.is_active:
                    next_status = "live"
                    next_session = session
                    break

                if session_start > now:
                    next_status = "upcoming"
                    next_session = session
                    break

                modules = course.modules.all()

                completed_count = ModuleProgress.objects.filter(
                    student=profile,
                    module__course=course,
                    completed=True
                ).count()

                total_modules = modules.count()

                progress_percent = 0
                if total_modules > 0:
                    progress_percent = int((completed_count / total_modules) * 100)

            enrolled_data.append({
                "course": course,
                "modules": modules,
                "status": next_status,
                "session": next_session,
                "progress_percent": progress_percent
            })

        return render(request, "courses/home.html", {
            "role": "student",
            "enrolled_data": enrolled_data,
            "available_courses": available_courses,
        })

    # ===============================
    # TEACHER DASHBOARD
    # ===============================
    if profile.role == "teacher":

        teaching_courses = Course.objects.filter(
            teacher=user
        )

        return render(request, "courses/home.html", {
            "role": "teacher",
            "teaching_courses": teaching_courses,
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