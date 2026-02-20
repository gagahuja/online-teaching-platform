from django.contrib import admin
from .models import Course, ClassSession, Enrollment, StudentProfile, Attendance, Module


admin.site.site_header = "Score Skill Admin"
admin.site.site_title = "Score Skill Portal"
admin.site.index_title = "Welcome to Score Skill Administration"


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'teacher', 'is_free', 'price', 'created_at')


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'description', 'order', 'course', 'created_at')


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
    list_filter = ("course", "scheduled_date", "is_active")
    search_fields = ("title", "meeting_room")


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




