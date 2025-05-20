from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, AthleteProfile, AthleteAccountReference
from allauth.account.models import EmailAddress
from import_export import resources
from import_export.admin import ImportExportModelAdmin

# Register your models here.

# Inline buat manage email verification
class EmailAddressInline(admin.TabularInline):
    model = EmailAddress
    extra = 0
    readonly_fields = ('email',)
    fields = ('email', 'verified', 'primary')
    can_delete = True

# Buat import (resource) file excel ke database referensi atlet
class AthleteAccountReferenceResource(resources.ModelResource):
    class Meta:
        model = AthleteAccountReference
        # Use nickname+ptm as the unique key for imports
        import_id_fields = ("nickname", "ptm")
        # Only insert new rows; skip rows that match exactly
        skip_unchanged = True
        report_skipped = True
        # Fields to include in import/export
        fields = ("nickname", "ptm", "divisi", "sudah_ada_akun")

    # Override default pencarian-exact biar bisa case-insensitive
    def get_instance(self, instance_loader, row):
        nickname = str(row.get("nickname", "")).strip()
        ptm      = str(row.get("ptm", "")).strip()
        # Try to fetch an existing record ignoring case
        return AthleteAccountReference.objects.filter(
            nickname__iexact=nickname,
            ptm__iexact=ptm
        ).first()  # returns None kalo ga ketemu

# Masukin database buat referensi atlet (pas daftar)
@admin.register(AthleteAccountReference)
class AthleteAccountReferenceAdmin(ImportExportModelAdmin):
    resource_class  = AthleteAccountReferenceResource
    list_display    = ("nickname", "ptm", "divisi", "sudah_ada_akun")
    list_filter     = ("sudah_ada_akun", "ptm")
    search_fields   = ("nickname", "ptm", "divisi")

# Buat bikin custom admin view di admin:index (alias dashboard admin)
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'nickname', 'real_name', 'ptm', 'role', 'is_active', 'is_staff', 'is_superuser')
    list_filter = (
        'role', 'is_active', 'is_staff', 'is_superuser',
    )

    # Inline email addresses for verification status
    inlines = [EmailAddressInline]

    # Extend the default fieldsets to include the role
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('profile_image', 'email', 'nickname', 'real_name', 'ptm')}),
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

admin.site.register(AthleteProfile)