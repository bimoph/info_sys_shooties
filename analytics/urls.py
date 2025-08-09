
from django.urls import path
from . import views

urlpatterns = [
    # path('', views.view_order, name='view_order'),
    
    path('', views.analytics_dashboard, name='analytics_dashboard'),
    path('operations/', views.operations_dashboard, name='operations_dashboard'),  # new operations page

]
