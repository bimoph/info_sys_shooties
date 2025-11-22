from django.db import models
from django.utils import timezone
from datetime import timedelta
from core.models import Store

class Employee(models.Model):
    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='employee_photos/', blank=True, null=True)
    daily_salary = models.PositiveIntegerField()
    # stores = models.ManyToManyField(Store, related_name='employees', blank=True)

    # current_balance = models.PositiveIntegerField(default=0

    def __str__(self):
        return self.name


class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    check_in = models.DateTimeField()
    check_out = models.DateTimeField(null=True, blank=True)

    check_in_photo = models.ImageField(upload_to='checkin_photos/', null=True, blank=True)
    check_out_photo = models.ImageField(upload_to='checkout_photos/', null=True, blank=True)
    payroll = models.ForeignKey('Payroll', on_delete=models.SET_NULL, null=True, blank=True, related_name='attendances')




    def duration_in_hours(self):
        if self.check_out:
            delta = self.check_out - self.check_in
            return delta.total_seconds() / 3600
        return 0

    def salary_earned(self):
        hours = self.duration_in_hours()
        full_day = self.employee.daily_salary
        if hours >= 9:
            return full_day
        elif hours >= 8.5:
            return full_day - 10000
        elif hours >= 5:
            return full_day // 2
        return 0

    def __str__(self):
        return f"{self.employee.name} - {self.check_in.date()}"

class Payroll(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    period_start = models.DateField(blank=True, null=True)
    period_end = models.DateField(blank=True, null=True)
    total_paid = models.IntegerField(blank=True, null=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.employee.name} - {self.period_start} to {self.period_end}"
