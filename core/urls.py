"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('enroll/<int:course_id>/', views.enroll_course, name='enroll_course'),
    path('toggle-session/<int:session_id>/', views.toggle_session, name='toggle_session'),
    path('live/<int:session_id>/', views.live_class, name='live_class'),
    path('toggle-module/<int:module_id>/',views.toggle_module_completion,name='toggle_module_completion'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('certificate/<int:course_id>/',views.download_certificate,name='download_certificate'),
    path('', include('courses.urls')),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/course/create/', views.create_course, name='create_course'),
    path('teacher/course/<int:course_id>/module/add/',views.add_module,name='add_module'),
    path('teacher/course/<int:course_id>/session/add/',views.add_session,name='add_session'),
    path('teacher/create-course/', views.create_course, name='create_course'),
    path('course/create/', views.create_course, name='create_course'),
    path('course/<int:course_id>/module/add/', views.add_module, name='add_module'),
    path('course/<int:course_id>/manage/',views.manage_course,name='manage_course'),
    path('course/<int:course_id>/session/add/',views.add_session,name='add_session'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('teacher/live/<int:session_id>/',views.teacher_live_panel,name='teacher_live_panel'),
    path('teacher/session/<int:session_id>/toggle/', views.toggle_session_status, name='toggle_session_status'),
    path("teacher/start-session/<int:session_id>/", views.start_session, name="start_session"),
    path("teacher/stop-session/<int:session_id>/", views.stop_session, name="stop_session"),
]


