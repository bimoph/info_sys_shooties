from django.db import models
from django.utils import timezone
from datetime import timedelta
from core.models import Store
from sales.models import Order, OrderItem
from django.db.models import Sum

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
        # --- BASE SALARY LOGIC (your original rules) ---
        hours = self.duration_in_hours()
        full_day = self.employee.daily_salary
        print(f"Calculating salary for {self.employee.name} with {full_day} daily salary.")
        if hours >= 9:
            base_salary = full_day
        elif hours >= 8.5:
            base_salary = full_day - 10000
        elif hours >= 5:
            base_salary = full_day // 2
        else:
            base_salary = 0

        # --- SALES CALCULATION ---
        # Get the date of the attendance
        attendance_date = self.check_in.date()
        print(f"Attendance date: {attendance_date}")
        print(f"Employee's store: {self.store}")
        
        # Get all orders for this store on this date
        orders = Order.objects.filter(
            store=self.store,
            served_at__date=attendance_date
        )

        # Sum quantities via OrderItem
        total_cups = OrderItem.objects.filter(
            order__in=orders
        ).aggregate(total=Sum('quantity'))['total'] or 0
        print(f"Total cups sold on {attendance_date} at store {self.store}: {total_cups}")
        # --- BONUS RULES ---
        bonus = 0
        if total_cups > 100:
            bonus += 30000  # base bonus
            bonus += (total_cups - 100) * 1000  # extra per cup

        return base_salary + bonus

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
