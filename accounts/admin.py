from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, AthleteProfile

# Register your models here.

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'role', 'is_staff', 'is_superuser')
    
    # Extend the default fieldsets to include the role
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )
    
    # Also include role when creating a new user in the admin
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role',)}),
    )