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
        if request.FILES.get('profile_image'):
            user.profile_image = request.FILES['profile_image']
        user.username = generate_unique_username(8)
        if commit:
            logger.debug("P1 : MyAccountAdapter.save_user: commit=True, about to save user & create profile")
            user.save()
            logger.debug("P2 : MyAccountAdapter.save_user: commit=True, about to save user & create profile")
        if user.role == "atlet":
            profile, created = AthleteProfile.objects.get_or_create(user=user)
            logger.debug("P3 : MyAccountAdapter.save_user: commit=True, about to save user & create profile")
        return user
