from django.shortcuts import render, redirect, get_object_or_404
from .models import Employee, Attendance, Payroll
from django.utils.timezone import is_naive, make_aware, now
from django.utils import timezone
from datetime import datetime
from datetime import date, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Min, Max
import pytz

from .forms import AttendanceCheckInForm, AttendanceCheckOutForm


@login_required
def attendance_list(request):
    user = request.user

    # Jakarta timezone
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    today_jakarta = now().astimezone(jakarta_tz).date()

    if user.role == 'cashier':
        records = Attendance.objects.select_related('employee').filter(check_in__date=today_jakarta, store=request.user.store).order_by('-check_in')
    else:
        records = Attendance.objects.select_related('employee').filter(store=request.user.store).order_by('-check_in')

    # Get filter values from request GET parameters
    employee_id = request.GET.get('employee')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Filter by employee
    if employee_id:
        records = records.filter(employee_id=employee_id)

    # Filter by date range
    if start_date and end_date:
        records = records.filter(check_in__date__range=[start_date, end_date])
    elif start_date:  # only start date
        records = records.filter(check_in__date__gte=start_date)
    elif end_date:  # only end date
        records = records.filter(check_in__date__lte=end_date)

    # Calculate hours worked
    for record in records:
        if record.check_out:
            duration = record.check_out - record.check_in
        else:
            duration = now() - record.check_in
        record.hours_worked = round(duration.total_seconds() / 3600, 2)

    if request.method == 'POST':
        selected_ids = request.POST.getlist('attendance_ids')
        print(f"DEBUG: Selected IDs: {selected_ids}")  # Debugging line
        if not selected_ids:
            return redirect('attendance_list')

        selected_attendances = Attendance.objects.filter(id__in=selected_ids, payroll__isnull=True)
        employees = set(a.employee_id for a in selected_attendances)
        if len(employees) > 1:
            return render(request, 'employee/attendance_list.html', {
                'records': records,
                'error': 'You can only create payroll for one employee at a time.'
            })

        employee = selected_attendances.first().employee
        period_start = selected_attendances.aggregate(Min('check_in'))['check_in__min'].date()
        period_end = selected_attendances.aggregate(Max('check_in'))['check_in__max'].date()
        total_paid = sum(a.salary_earned() for a in selected_attendances)

        payroll = Payroll.objects.create(
            employee=employee,
            period_start=period_start,
            period_end=period_end,
            total_paid=total_paid
        )

        selected_attendances.update(payroll=payroll)
        return redirect('payroll_detail', pk=payroll.pk)

    return render(request, 'employee/attendance_list.html', {
        'records': records,
        'employees': Employee.objects.all(),
        'role': request.user.role,
    })


# 2. Payroll List
@login_required
def payroll_list(request):
    payrolls = Payroll.objects.select_related('employee').order_by('-period_start')
    return render(request, 'employee/payroll_list.html', {'payrolls': payrolls, 'role': request.user.role,})


# 3. Payroll Detail
@login_required
def payroll_detail(request, pk):
    payroll = get_object_or_404(Payroll, pk=pk)
    print(f"DEBUG: Payroll ID: {payroll.id}, Employee: {payroll.employee.name}")  # Debugging line
    attendances = payroll.attendances.all()  # uses related_name from Attendance model
    print(f"DEBUG: Number of attendances: {attendances.count()}")  # Debugging line
    return render(request, 'employee/payroll_detail.html', {
        'payroll': payroll,
        'attendances': attendances,
        'role': request.user.role,
    })


# 4. Pay Salary
@login_required
def pay_salary(request, pk):
    payroll = get_object_or_404(Payroll, pk=pk)
    if not payroll.is_paid:
        payroll.is_paid = True
        payroll.paid_at = now()
        # payroll.employee.current_balance += payroll.total_paid
        # payroll.employee.save()
        payroll.save()
    return redirect('payroll_detail', pk=pk)





@login_required
def check_in(request):
    if request.method == 'POST':
        form = AttendanceCheckInForm(request.POST, request.FILES)
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.check_in = timezone.now()
            attendance.save()
            return redirect('attendance_list')
    else:
        form = AttendanceCheckInForm()
    return render(request, 'employee/check_in.html', {'form': form, 'role': request.user.role,})

@login_required
def check_out(request, attendance_id):
    attendance = get_object_or_404(Attendance, id=attendance_id)
    if request.method == 'POST':
        form = AttendanceCheckOutForm(request.POST, request.FILES, instance=attendance)
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.check_out = timezone.now()

            # Save uploaded check-out photo
            if 'check_out_photo' in request.FILES:
                attendance.check_out_photo = request.FILES['check_out_photo']

            # Update employee balance
            earned = attendance.salary_earned()
            # attendance.employee.current_balance += earned
            attendance.employee.save()

            attendance.save()
            return redirect('attendance_list')
    else:
        form = AttendanceCheckOutForm(instance=attendance)

    return render(request, 'employee/check_out.html', {'form': form, 'attendance': attendance, 'role': request.user.role,})

@login_required
def attendance_detail(request, pk):
    attendance = get_object_or_404(Attendance, pk=pk)
    return render(request, 'employee/attendance_detail.html', {'attendance': attendance, 'role': request.user.role,})








# PAYROLLLLLLL ---------


# def payroll_home(request):
#     employees = Employee.objects.all()
#     data = []

#     for emp in employees:
#         last_payroll = Payroll.objects.filter(employee=emp).order_by('-period_end').first()

#         if last_payroll:
#             period_start = last_payroll.period_end + timedelta(days=1)
#         else:
#             first_attendance = Attendance.objects.filter(employee=emp).order_by('check_in').first()
#             period_start = first_attendance.check_in.date() if first_attendance else None

#         if period_start:
#             last_attendance = Attendance.objects.filter(employee=emp, check_in__date__gte=period_start).order_by('-check_in').first()
#             period_end = last_attendance.check_in.date() if last_attendance else None
#         else:
#             period_end = None

#         data.append({
#             'employee': emp,
#             'current_balance': emp.current_balance,
#             'period_start': period_start,
#             'period_end': period_end,
#         })

#     return render(request, 'employee/payroll_home.html', {
#         'employee_data': data
#     })

# def employee_earned_summary(request, employee_id):
#     emp = get_object_or_404(Employee, pk=employee_id)
#     last_payroll = Payroll.objects.filter(employee=emp).order_by('-period_end').first()

#     if last_payroll:
#         period_start = last_payroll.period_end + timedelta(days=1)
#     else:
#         first_attendance = Attendance.objects.filter(employee=emp).order_by('check_in').first()
#         period_start = first_attendance.check_in.date() if first_attendance else None

#     if period_start:
#         attendances = Attendance.objects.filter(
#             employee=emp,
#             check_in__date__gte=period_start,
#             check_out__isnull=False
#         ).order_by('check_in')

#         total_salary = sum([a.salary_earned() for a in attendances])
#         period_end = attendances.last().check_in.date() if attendances else None
#     else:
#         attendances = []
#         total_salary = 0
#         period_end = None

#     return render(request, 'employee/employee_earned_summary.html', {
#         'employee': emp,
#         'attendances': attendances,
#         'total_salary': total_salary,
#         'period_start': period_start,
#         'period_end': period_end,
#         'can_payroll': total_salary > 0
#     })


# @csrf_exempt
# def create_payroll_from_summary(request, employee_id):
#     if request.method == 'POST':
#         employee = get_object_or_404(Employee, pk=employee_id)
#         start_date_raw = request.POST.get('start_date')
#         end_date_raw = request.POST.get('end_date')

#         try:
#             start_date = datetime.strptime(start_date_raw, "%Y-%m-%d").date()
#             end_date = datetime.strptime(end_date_raw, "%Y-%m-%d").date()
#         except ValueError:
#             return redirect('employee_earned_summary', employee_id=employee_id)

#         attendances = Attendance.objects.filter(
#             employee=employee,
#             check_in__date__gte=start_date,
#             check_in__date__lte=end_date,
#             check_out__isnull=False
#         )
#         total = sum([a.salary_earned() for a in attendances])

#         Payroll.objects.create(
#             employee=employee,
#             period_start=start_date,
#             period_end=end_date,
#             total_paid=total
#         )

#         employee.current_balance = 0
#         employee.save()

#         return redirect('payroll_detail', pk=employee.id)


# def payroll_detail(request, pk):
#     employee = get_object_or_404(Employee, pk=pk)
#     payrolls = Payroll.objects.filter(employee=employee).order_by('-period_end')

#     return render(request, 'employee/payroll_detail.html', {
#         'employee': employee,
#         'payrolls': payrolls
#     })
