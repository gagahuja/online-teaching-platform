from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from courses.models import Course, ClassSession, StudentProfile, Enrollment, Attendance
from django.utils.timezone import localtime
from datetime import datetime
from django.contrib.auth.models import User
from django.http import HttpResponse





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
    now = datetime.now()

    if user.is_staff:
        courses = Course.objects.filter(teacher=user)
    else:
        courses = Course.objects.filter(
            enrollment__student__user=user
        ).distinct()

    dashboard_data = []

    for course in courses:
        sessions_data = []

        for cls in course.sessions.all():

            session_start = datetime.combine(
                cls.scheduled_date,
                cls.start_time
            )

            session_end = datetime.combine(
                cls.scheduled_date,
                cls.end_time
            )

            if now < session_start:
                status = "upcoming"
            elif session_start <= now <= session_end:
                if cls.is_active:
                    status = "live"
                else:
                    status = "waiting"
            else:
                status = "ended"


            sessions_data.append({
                "id": cls.id,
                "title": cls.title,
                "scheduled_date": cls.scheduled_date,
                "start_time": cls.start_time,
                "end_time": cls.end_time,
                "status": status,
            })

        dashboard_data.append({
            "id": course.id,
            "title": course.title,
            "sessions": sessions_data
        })

    return render(request, 'courses/home.html', {
        'dashboard_data': dashboard_data
    })


from django.http import JsonResponse
from django.views.decorators.http import require_POST

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





