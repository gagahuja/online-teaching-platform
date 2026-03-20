from django.contrib import admin
from django.urls import path, include
from . import views
from courses.views import live_class
from django.http import HttpResponse


def health(request):
    return HttpResponse("OK")


urlpatterns = [
    path('admin/', admin.site.urls),

    #path('', views.home, name='home'),

    path('accounts/', include('django.contrib.auth.urls')),

    path('student/dashboard/', views.student_dashboard_v2, name='student_dashboard'),

    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),

    path('live/<int:session_id>/', live_class, name='live_class'),

    path('', include('courses.urls')),

    path('health/', health),
]