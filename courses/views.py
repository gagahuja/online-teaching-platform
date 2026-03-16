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

from .models import ClassSession, Attendance


@login_required
def live_class(request, session_id):

    session = get_object_or_404(ClassSession, id=session_id)

    # create attendance when student joins
    attendance, created = Attendance.objects.get_or_create(
        student=request.user,
        session=session,
        defaults={
            "join_time": timezone.now()
        }
    )

    context = {
        "session": session,
        "attendance": attendance
    }

    return render(request, "courses/live_class.html", context)