from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

class Store(models.Model):
    name = models.CharField(max_length=150)
    address = models.TextField(blank=True)
    type = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')


    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('cashier', 'Cashier'),
        ('manager', 'Manager'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='cashier')

    def __str__(self):
        return f"{self.username} ({self.role})"
    