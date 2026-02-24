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
@login_required
def home(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if request.user.is_staff:
        courses = Course.objects.filter(teacher=request.user)
    else:
        enrolled_ids = Enrollment.objects.filter(
            student=profile
        ).values_list('course_id', flat=True)

        courses = Course.objects.filter(id__in=enrolled_ids)

    dashboard_data = []
    now = localtime().replace(tzinfo=None)

    for course in courses:
        sessions_list = []

        for session in course.sessions.all():
            session_start = datetime.combine(
                session.scheduled_date,
                session.start_time
            )

            session_end = datetime.combine(
                session.scheduled_date,
                session.end_time
            )

            if now < session_start:
                status = "upcoming"
            elif session_start <= now <= session_end:
                if session.is_active:
                    status = "live"
                else:
                    status = "waiting"
            else:
                status = "ended"

            sessions_list.append({
                "id": session.id,
                "title": session.title,
                "scheduled_date": session.scheduled_date,
                "start_time": session.start_time,
                "end_time": session.end_time,
                "status": status
            })

        dashboard_data.append({
            "id": course.id,
            "title": course.title,
            "sessions": sessions_list
        })

    return render(request, "courses/home.html", {
        "dashboard_data": dashboard_data
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

    for session in course.sessions.all():
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



