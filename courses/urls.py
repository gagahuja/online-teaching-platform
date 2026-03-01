from django.urls import path
from core.views import live_class
from core.views import home, live_class, toggle_session
from core.views import home, live_class, toggle_session, course_attendance

urlpatterns = [
    path('', home, name='home'),               # 👈 HOME PAGE
    path('live/<int:session_id>/', live_class, name='live_class'),
    path('toggle-session/<int:session_id>/', toggle_session, name='toggle_session'),
    path('attendance/<int:course_id>/', course_attendance, name='course_attendance'),
   # path('enroll/<int:course_id>/', views.enroll_course, name='enroll_course'),
]

from django.urls import path
from core import views

urlpatterns = [

    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),

    path('teacher/course/create/', views.create_course, name='create_course'),

    path('teacher/course/<int:course_id>/module/add/',
         views.add_module,
         name='add_module'),

    path('teacher/course/<int:course_id>/session/add/',
         views.add_session,
         name='add_session'),
]