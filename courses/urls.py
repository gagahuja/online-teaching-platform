from django.urls import path
from .views import live_class, leave_class, download_attendance, enroll_course
from core.views import home, course_attendance
from core import views

urlpatterns = [

    path('', home, name='home'),

    path('live/<int:session_id>/', live_class, name='live_class'),

    path('attendance/<int:course_id>/', course_attendance, name='course_attendance'),

    path('attendance-report/<int:session_id>/', download_attendance, name='attendance_report'),

    path('leave-class/', leave_class, name='leave_class'),

    path('enroll/<int:course_id>/', enroll_course, name='enroll_course'),
]

urlpatterns += [

    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),

    path('teacher/course/create/', views.create_course, name='create_course'),

    path('teacher/course/<int:course_id>/module/add/', views.add_module, name='add_module'),

    path('teacher/course/<int:course_id>/session/add/', views.add_session, name='add_session'),

]