from django.db import models
from core.models import Store

class Ingredient(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='ingredients', blank=True, null=True)

    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=50, default='ml')  # could be ml, gram, pcs, etc.
    quantity_in_stock = models.FloatField(default=0)  # current stock
    low_stock_threshold = models.FloatField(default=10)  # for alerts

    def __str__(self):
        return f"{self.name} ({self.quantity_in_stock} {self.unit})"
   

class StockEntry(models.Model):
    # store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='stock_entries', blank=True, null=True)

    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=100, choices=[
        ('manual_add', 'Manual Addition'),
        ('manual_deduct', 'Manual Deduction'),
        ('sale_deduct', 'Sale Deduction'),
        ('sale_cancellation', 'Sale Cancellation'),
    ])

    def __str__(self):
        return f"{self.ingredient.name}: {self.quantity} ({self.reason})"

class SmoothieMenu(models.Model):
    stores = models.ManyToManyField(Store, related_name='smoothie_menus')

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.name

class SmoothieIngredient(models.Model):
    # store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='smoothie_ingredients', blank=True, null=True)

    smoothie = models.ForeignKey(SmoothieMenu, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.FloatField()  # how much of the ingredient is used per order

    class Meta:
        unique_together = ('smoothie', 'ingredient')

    def __str__(self):
        return f"{self.amount} {self.ingredient.unit} of {self.ingredient.name} in {self.smoothie.name}"

