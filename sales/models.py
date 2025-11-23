from django.db import models
from inventory.models import SmoothieMenu
from django.utils import timezone
from customers.models import Customer
from core.models import Store


class PaymentMethod(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Order(models.Model):

    # PAYMENT_METHOD_CHOICES = [
    #     ('cash', 'Cash'),
    #     ('qris', 'QRIS'),
    #     # Add more if needed
    # ]
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)

    name = models.CharField(max_length=20)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)

    total_price = models.IntegerField()
    # payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='qris')
    payment_method = models.ForeignKey(
        PaymentMethod, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=False     ,
    )
    is_ready = models.BooleanField(default=False)
    is_served = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    served_at = models.DateTimeField(null=True, blank=True)

    list_menu = models.ManyToManyField(SmoothieMenu, through='OrderItem')

    def mark_ready(self):
        self.is_ready = True
        self.ready_at = timezone.now()
        self.save()

    def mark_served(self):
        self.is_served = True
        self.served_at = timezone.now()
        self.save()

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    smoothie = models.ForeignKey(SmoothieMenu, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

