from django.contrib import admin
from .models import Customer, Passport
# Register your models here.
admin.site.register(Customer)


@admin.register(Passport)
class PassportAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'stamps', 'free_claimed', 'claimed_at', 'created_at')
    list_filter = ('free_claimed',)
    search_fields = ('customer__name', 'customer__phone')
