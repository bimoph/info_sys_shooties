from django.contrib import admin

# Register your models here.
from .models import Order, OrderItem, PaymentMethod

admin.site.register(PaymentMethod)
admin.site.register(Order)
admin.site.register(OrderItem)
