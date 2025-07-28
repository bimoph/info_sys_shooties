from django.contrib import admin

# Register your models here.
from .models import Ingredient, StockEntry, SmoothieMenu, SmoothieIngredient

admin.site.register(Ingredient)
admin.site.register(StockEntry)
admin.site.register(SmoothieMenu)
admin.site.register(SmoothieIngredient)


