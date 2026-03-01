from django import forms
from .models import Course

class CourseForm(forms.ModelForm):

    class Meta:
        model = Course
        fields = ['title', 'description', 'price']


from .models import Module

class ModuleForm(forms.ModelForm):

    class Meta:
        model = Module
        fields = ['title', 'description', 'order']


from .models import ClassSession

class SessionForm(forms.ModelForm):

    class Meta:
        model = ClassSession
        fields = [
            'title',
            'scheduled_date',
            'start_time',
            'end_time',
            'meeting_room'
        ]