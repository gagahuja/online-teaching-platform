from django.contrib import admin
from .models import Course, ClassSession, Enrollment, StudentProfile, Attendance

admin.site.site_header = "Score Skill Admin"
admin.site.site_title = "Score Skill Portal"
admin.site.index_title = "Welcome to Score Skill Administration"


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'is_free', 'price', 'created_at')


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "course",
        "scheduled_date",
        "start_time",
        "end_time",
        "is_active",
        "meeting_room",
    )


admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(StudentProfile)
admin.site.register(Attendance)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'joined_at')
    list_filter = ('session',)

