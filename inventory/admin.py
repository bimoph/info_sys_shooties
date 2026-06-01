from django.contrib import admin
from .models import Ingredient, StockEntry, SmoothieMenu, SmoothieIngredient, AddOn


class AddOnInline(admin.TabularInline):
    model = AddOn
    extra = 1
    fields = ('name', 'price', 'is_active')


class SmoothieMenuAdmin(admin.ModelAdmin):
    inlines = [AddOnInline]


admin.site.register(Ingredient)
admin.site.register(StockEntry)
admin.site.register(SmoothieMenu, SmoothieMenuAdmin)
admin.site.register(SmoothieIngredient)
admin.site.register(AddOn)


