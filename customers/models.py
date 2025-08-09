
from django.db import models



class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, unique=True)
    joined_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_orders(self):
        return self.orders.all()
    
    def total_spent(self, start_date=None, end_date=None):
        orders = self.order_set.all()

        if start_date:
            orders = orders.filter(created_at__gte=start_date)
        if end_date:
            orders = orders.filter(created_at__lte=end_date)

        return sum(order.total_price for order in orders)
