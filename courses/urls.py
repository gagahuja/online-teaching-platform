from django.urls import path
from core.views import live_class
from core.views import home, live_class, toggle_session
from core.views import home, live_class, toggle_session, course_attendance

urlpatterns = [
    path('', home, name='home'),               # 👈 HOME PAGE
    path('live/<int:session_id>/', live_class, name='live_class'),
    path('toggle-session/<int:session_id>/', toggle_session, name='toggle_session'),
    path('attendance/<int:course_id>/', course_attendance, name='course_attendance'),
]

