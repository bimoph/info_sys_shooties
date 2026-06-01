"""
URL configuration for shooties_pos project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core.views import home, no_permission
from customers import views as views_customers
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', home, name='home'),
    path('no-permission/', no_permission, name='no_permission'),
    path("admin/", admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('inventory/', include('inventory.urls')),
    path('customers/', include('customers.urls')),
    path('employee/', include('employee.urls')),
    path('sales/', include('sales.urls')),
    path('analytics/', include('analytics.urls')),
    path('register/', views_customers.register_customer, name='customer_register'),
    path('<str:phone>/passport/claim/', views_customers.passport_claim, name='passport_claim'),
    path('<str:phone>/', views_customers.member_profile, name='member_profile'),
    

]





urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)