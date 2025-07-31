from django.urls import path
from . import views

urlpatterns = [
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('check-in/', views.check_in, name='check_in'),
    path('check-out/<int:attendance_id>/', views.check_out, name='check_out'),
    path('attendance/<int:pk>/', views.attendance_detail, name='attendance_detail'),

    path('payroll/', views.payroll_home, name='payroll_home'),
    path('earned-summary/<int:employee_id>/', views.employee_earned_summary, name='employee_earned_summary'),
    path('create-payroll-summary/<int:employee_id>/', views.create_payroll_from_summary, name='create_payroll_from_summary'),

    path('payroll-detail/<int:pk>/', views.payroll_detail, name='payroll_detail'),

]
