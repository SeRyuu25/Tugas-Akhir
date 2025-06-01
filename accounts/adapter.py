from allauth.account.adapter import DefaultAccountAdapter
from django.core.exceptions import ValidationError
from .models import CustomUser, AthleteProfile
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model

import logging
logger = logging.getLogger(__name__)

# Utility buat ngecek username udh dipake ato belum (untuk registrasi akun)
def generate_unique_username(length=8):
    User = get_user_model()
    username = get_random_string(length)
    while User.objects.filter(username=username).exists():
        username = get_random_string(length)
    return username

# Adapter buat bikin akun atlet
class MyAccountAdapter(DefaultAccountAdapter):
    # Buat cek nama panggilan harus unik (tidak tergantung besar / kecil huruf)
    def clean_nickname(self, nickname):
        qs = CustomUser.objects.filter(nickname__iexact=nickname)
        if self.request.user.is_authenticated:
            qs = qs.exclude(pk=self.request.user.pk)
        if qs.exists():
            raise ValidationError("Nama panggilan sudah dipakai.")
        return nickname

    # Buat simpan akun atlet baru
    def save_user(self, request, user, form, commit=True):
        # ini yang dari allauth
        user = super().save_user(request, user, form, commit=False)

        user.role = 'atlet'
        user.nickname  = form.cleaned_data.get("nickname", "")
        user.real_name = form.cleaned_data.get("real_name", "")
        
        profile_image_file = form.cleaned_data.get('profile_image')
        if profile_image_file:
            user.profile_image = profile_image_file
        elif 'profile_image' in form.changed_data and not profile_image_file:
            user.profile_image = None

        user.username = generate_unique_username(8)

        if commit:
            try:
                user.save()
                
                if user.role == "atlet":
                    profile, created = AthleteProfile.objects.get_or_create(user=user)
                        
            except Exception as e:
                # Log kalo tiba" error
                logger.error(f"ADAPTER_ERROR: Error during user.save() or AthleteProfile creation in adapter for user {user.username if user.username else 'unknown'}: {e}", exc_info=True)
                raise
        else:
            # Log kalo commitnya entah kenpaa false
            logger.info(f"ADAPTER_INFO: Commit is False for user {user.username if user.username else 'unknown'}. User object not saved by adapter at this stage.")
            
        return user
