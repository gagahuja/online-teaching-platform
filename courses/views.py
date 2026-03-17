import csv
from django.http import HttpResponse
from .models import Attendance


def download_attendance(request, session_id):

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_report.csv"'

    writer = csv.writer(response)

    writer.writerow([
        "Student",
        "Join Time",
        "Leave Time",
        "Duration (minutes)"
    ])

    records = Attendance.objects.filter(session_id=session_id)

    for record in records:

        duration = record.duration_minutes()

        writer.writerow([
            record.student.username,
            record.join_time,
            record.leave_time,
            round(duration, 2) if duration else ""
        ])

    return response


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import ClassSession, Attendance, StudentProfile

@login_required
def live_class(request, session_id):

    session = get_object_or_404(ClassSession, id=session_id)

    profile, created = StudentProfile.objects.get_or_create(
        user=request.user,
        defaults={"role": "student"}
    )

    user_role = profile.role

    attendance, created = Attendance.objects.get_or_create(
        student=request.user,
        session=session,
        defaults={
            "join_time": timezone.now()
        }
    )

    context = {
        "session": session,
        "attendance": attendance,
        "user_role": user_role,
        "meeting_name": f"ScoreSkill_{session.id}"
    }

    return render(request, "courses/live_class.html", context)



import json
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from .models import Attendance


@csrf_exempt  # required for sendBeacon
@login_required
def leave_class(request):

    if request.method == "POST":

        try:
            data = json.loads(request.body)

            session_id = data.get("session_id")

            attendance = Attendance.objects.filter(
                student=request.user,
                session_id=session_id,
                leave_time__isnull=True
            ).last()

            if attendance:
                attendance.leave_time = timezone.now()
                attendance.save()

            return JsonResponse({"status": "success"})

        except Exception as e:
            return JsonResponse({"error": str(e)})

    return JsonResponse({"error": "Invalid request"})