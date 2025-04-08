from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, IPRatingOpinion

# Buat registrasi Atlet aja
class AthleteAccountCreationForm(UserCreationForm):
    real_name = forms.CharField(required=True, max_length=100)
    profile_image = forms.ImageField(required=False)
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # Pasang field data yang dibutuhin buat registrasi atlet
        fields = ('profile_image', 'username', 'real_name', 'email')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Role fix jadi buat atlet aja
        user.role = 'atlet'
        if commit:
            user.save()
        return user

# Buat registrasi IP account
class IPAccountCreationForm(UserCreationForm):
    real_name = forms.CharField(required=True, max_length=100)
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'real_name', 'email',)

    def save(self, commit=True):
        user = super().save(commit=False)
        # Role fix jadi buat IP aja
        user.role = 'ip'
        if commit:
            user.save()
        return user

# Buat masukin initial rating dari IP
class IPRatingOpinionForm(forms.ModelForm):
    class Meta:
        model = IPRatingOpinion
        fields = ['opinion_rating']

class ManualIPOpinionForm(forms.ModelForm):
    class Meta:
        model = IPRatingOpinion
        fields = ['athlete_identifier', 'opinion_rating']

class CustomUserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'real_name', 'email', 'profile_image']
