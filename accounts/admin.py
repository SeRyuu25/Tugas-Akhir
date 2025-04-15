from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, AthleteProfile

# Register your models here.

# Buat bikin custom admin view di admin:index (alias dashboard admin)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'nickname', 'real_name', 'role', 'is_staff', 'is_superuser')
    
    # Extend the default fieldsets to include the role
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('profile_image', 'email', 'nickname', 'real_name')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Also include role when creating a new user in the admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'nickname', 'real_name', 'email', 'role', 'password1', 'password2'),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(AthleteProfile)