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

        duration = ""

        if record.leave_time:
            duration = (record.leave_time - record.join_time).total_seconds() / 60

        writer.writerow([
            record.student.username,
            record.join_time,
            record.leave_time,
            round(duration, 2) if duration else ""
        ])

    return response