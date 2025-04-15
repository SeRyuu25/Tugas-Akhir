from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, IPRatingOpinion
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model

# Utility buat ngecek username udh dipake ato belum (untuk registrasi akun)
User = get_user_model()
def generate_unique_username(length=8):
    username = get_random_string(length)
    while User.objects.filter(username=username).exists():
        username = get_random_string(length)
    return username

# Buat registrasi Atlet aja
class AthleteAccountCreationForm(UserCreationForm):
    nickname = forms.CharField(required=True, max_length=100)
    real_name = forms.CharField(required=True, max_length=100)
    profile_image = forms.ImageField(required=False)
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # Pasang field data yang dibutuhin buat registrasi atlet
        fields = ('profile_image', 'nickname', 'real_name', 'email')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Role fix jadi buat atlet aja
        user.role = 'atlet'
        user.username = generate_unique_username(8)
        if commit:
            user.save()
        return user

# Buat registrasi IP account
class IPAccountCreationForm(UserCreationForm):
    nickname = forms.CharField(required=True, max_length=100)
    real_name = forms.CharField(required=True, max_length=100)
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('nickname', 'real_name', 'email',)

    def save(self, commit=True):
        user = super().save(commit=False)
        # Role fix jadi buat IP aja
        user.role = 'ip'
        user.username = generate_unique_username(8)
        if commit:
            user.save()
        return user

# Buat masukin initial rating dari IP
class IPRatingOpinionForm(forms.ModelForm):
    class Meta:
        model = IPRatingOpinion
        fields = ['opinion_rating']

# Buat update profile
class CustomUserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['profile_image', 'nickname', 'real_name', 'email']

# Buat masukin initial rating yang manual (data atlet blom ada)
class ManualIPOpinionForm(forms.ModelForm):
    class Meta:
        model = IPRatingOpinion
        fields = ['athlete_identifier', 'opinion_rating']


