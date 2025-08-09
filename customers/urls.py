from django.urls import path
from . import views

urlpatterns = [
    path('', views.customer_list, name='customer_list'),
    path('add/', views.add_customer, name='add_customer'),
    path('<int:pk>/', views.customer_detail, name='customer_detail'),
    path('<int:pk>/delete/', views.delete_customer, name='delete_customer'),
    path('<int:pk>/edit/', views.edit_customer, name='edit_customer'),  

    path('spending/', views.customer_spending_report, name='customer_spending_report'),

    # ajaxxxx
    path('check-phone/', views.check_phone, name='customers_check_phone'),
    path('create-ajax/', views.create_customer_ajax, name='customers_create_ajax'),


]
