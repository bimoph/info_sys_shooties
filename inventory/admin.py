from django.contrib import admin
from .models import Ingredient, StockEntry, SmoothieMenu, SmoothieIngredient, AddOn


class AddOnMenuInline(admin.TabularInline):
    # Attach existing add-ons to this menu (M2M through table).
    model = AddOn.menus.through
    extra = 1
    verbose_name = "Add-on"
    verbose_name_plural = "Add-ons on this menu"


class SmoothieMenuAdmin(admin.ModelAdmin):
    inlines = [AddOnMenuInline]


class AddOnAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_active')
    list_filter = ('is_active', 'menus')
    search_fields = ('name',)
    filter_horizontal = ('menus',)


admin.site.register(Ingredient)
admin.site.register(StockEntry)
admin.site.register(SmoothieMenu, SmoothieMenuAdmin)
admin.site.register(SmoothieIngredient)
admin.site.register(AddOn, AddOnAdmin)


