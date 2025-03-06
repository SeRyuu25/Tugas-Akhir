from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

# Buat registrasi Atlet aja
class AthleteAccountCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # Pasang field data yang dibutuhin buat registrasi atlet
        fields = ('username', 'email',)
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Role fix jadi buat atlet aja
        user.role = 'atlet'
        if commit:
            user.save()
        return user

# Buat registrasi IP account
class IPAccountCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email',)

    def save(self, commit=True):
        user = super().save(commit=False)
        # Role fix jadi buat IP aja
        user.role = 'ip'
        if commit:
            user.save()
        return user