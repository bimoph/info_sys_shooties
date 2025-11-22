from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import User, Store
class CustomUserAdmin(UserAdmin):
    model = User
    add_form = UserCreationForm
    form = UserChangeForm

    # -----------------------------
    # 1. Add "role" to list display
    # -----------------------------
    list_display = ('username', 'email', 'role', 'store', 'is_staff', 'is_active')
    list_filter = ('role', 'store', 'is_staff', 'is_active')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),

        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email')
        }),

        ('Store & Role info', {
            'fields': ('store', 'role')     # <-- ADD ROLE HERE
        }),

        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),

        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    # -----------------------------
    # 2. Add "role" to add form
    # -----------------------------
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'password1',
                'password2',
                'store',
                'role',            # <-- ADD ROLE HERE
                'is_active',
                'is_staff'
            ),
        }),
    )

    search_fields = ('username', 'email')
    ordering = ('username',)


admin.site.register(User, CustomUserAdmin)
admin.site.register(Store)