from django import forms
from .models import Attendance

class AttendanceCheckInForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['employee', 'check_in_photo']


class AttendanceCheckOutForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['check_out_photo']