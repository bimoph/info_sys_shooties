
from django.db import models



class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    joined_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name
