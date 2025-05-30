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
            # ---- ADD LOGGING HERE ----
            logger.info(f"ADAPTER_DEBUG: Profile image found in request.FILES.")
            logger.info(f"ADAPTER_DEBUG: File name: {profile_image_file.name}")
            logger.info(f"ADAPTER_DEBUG: File size: {profile_image_file.size}")
            logger.info(f"ADAPTER_DEBUG: File content type: {profile_image_file.content_type}")
            # ---- END LOGGING ----
            user.profile_image = profile_image_file
        elif 'profile_image' in form.changed_data and not profile_image_file: # Field was cleared
            logger.info("ADAPTER_DEBUG: Profile image field was present in form and cleared by user.")
            user.profile_image = None

        user.username = generate_unique_username(8)

        if commit:
            logger.info(f"ADAPTER_DEBUG: Commit is True. Attempting to save user. Profile image field value: {getattr(user, 'profile_image', 'Not Set')}")
            try:
                user.save() # This is where the ImageField saving (and Cloudinary upload) happens
                logger.info(f"ADAPTER_DEBUG: User (pk={user.pk}) saved successfully in adapter.")
                
                # Create AthleteProfile only after user is saved and has an ID, and if role is 'atlet'
                if user.role == "atlet":
                    profile, created = AthleteProfile.objects.get_or_create(user=user)
                    if created:
                        logger.info(f"ADAPTER_DEBUG: AthleteProfile created for user {user.username} (pk={user.pk}).")
                    else:
                        logger.info(f"ADAPTER_DEBUG: AthleteProfile already existed for user {user.username} (pk={user.pk}).")
                        
            except Exception as e:
                logger.error(f"ADAPTER_DEBUG: Error during user.save() or AthleteProfile creation in adapter: {e}", exc_info=True)
                raise # Re-raise the exception so Django's error handling (and DEBUG page) can show it
        else:
            logger.info("ADAPTER_DEBUG: Commit is False. User object not saved by adapter at this stage.")
        
        return user
