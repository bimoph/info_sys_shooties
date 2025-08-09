from django.urls import path
from . import views

urlpatterns = [
    path('', views.view_order, name='view_order'),
    path('order_list/', views.order_list, name='order_list'),
    path('create-order', views.create_order, name='create_order'),
    path('mark-ready/<int:order_id>/', views.mark_ready, name='mark_ready'),
    path('mark-served/<int:order_id>/', views.mark_served, name='mark_served'),
    path('move-to-pending/<int:order_id>/', views.move_to_pending, name='move_to_pending'),
    path('move-to-ready/<int:order_id>/', views.move_to_ready, name='move_to_ready'),
    path('delete-order/<int:order_id>/', views.delete_order, name='delete_order'),
]
