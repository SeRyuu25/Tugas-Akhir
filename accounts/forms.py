from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, IPRatingOpinion, AthleteAccountReference
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model
from allauth.account.forms import SignupForm, LoginForm
from allauth.account.models import EmailAddress

# Utility buat ngecek username udh dipake ato belum (untuk registrasi akun)
User = get_user_model()
def generate_unique_username(length=8):
    username = get_random_string(length)
    while User.objects.filter(username=username).exists():
        username = get_random_string(length)
    return username

# Buat signup form
class CustomSignupForm(SignupForm):
    nickname      = forms.CharField(
        max_length=100,
        label="Nama Panggilan",
        widget=forms.TextInput(attrs={'class':'form-control'}),
    )
    real_name     = forms.CharField(
        max_length=100,
        label="Nama Lengkap",
        widget=forms.TextInput(attrs={'class':'form-control'}),
    )
    profile_image = forms.ImageField(
        label="Foto Profil",
        required=False,
        widget=forms.ClearableFileInput(attrs={'class':'form-control'})
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        # Check *all* addresses (verified or not) so you can’t reuse an unconfirmed one either
        if EmailAddress.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Alamat email ini sudah terdaftar. Silakan gunakan email lain."
            )
        return email

    def save(self, request):
        # Let allauth create the user (email & password)
        user = super().save(request)
        # Now save our extra fields
        user.nickname      = self.cleaned_data['nickname']
        user.real_name     = self.cleaned_data['real_name']
        if self.cleaned_data.get('profile_image'):
            user.profile_image = self.cleaned_data['profile_image']
        user.save()
        return user

# Buat cek dari referensi atlet (pas pendaftaran atlet)
class ReferenceCheckForm(forms.Form):
    nickname = forms.CharField(max_length=100, label="Nama Panggilan")
    ptm      = forms.CharField(max_length=100, label="Nama PTM")

    def clean(self):
        cleaned = super().clean()
        nick, ptm = cleaned.get("nickname"), cleaned.get("ptm")
        try:
            ref = AthleteAccountReference.objects.get(nickname__iexact=nick, ptm__iexact=ptm)
        except AthleteAccountReference.DoesNotExist:
            cleaned["is_new"] = True
        else:
            if ref.sudah_ada_akun:
                raise forms.ValidationError("Kombinasi ini sudah terpakai akun.")
            cleaned["reference"] = ref
            cleaned["is_new"] = False
        return cleaned

# Buat registrasi IP account
class IPAccountCreationForm(UserCreationForm):
    nickname  = forms.CharField(required=True, max_length=100)
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
class CustomAccountUpdateForm(forms.ModelForm):
    class Meta:
        model  = CustomUser
        fields = ['profile_image', 'nickname', 'real_name']

    def clean_nickname(self):
        nick = self.cleaned_data.get("nickname")
        qs   = CustomUser.objects.filter(nickname__iexact=nick).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Nama panggilan sudah dipakai.")
        return nick

# Buat masukin initial rating yang manual (data atlet blom ada)
class ManualIPOpinionForm(forms.ModelForm):
    class Meta:
        model = IPRatingOpinion
        fields = ['athlete_identifier', 'opinion_rating']


