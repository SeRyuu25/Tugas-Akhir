from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from .models import CustomUser, IPRatingOpinion, AthleteAccountReference
from django.utils.crypto import get_random_string
from django.utils.safestring import mark_safe
from django.contrib.auth import get_user_model
from allauth.account.forms import SignupForm
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
        widget=forms.ClearableFileInput(attrs={'class':'form-control'}),
        help_text="Ukuran file maksimal 2MB. Format yang disarankan: JPG, PNG.",
    )

    def __init__(self, *args, **kwargs):
        super(CustomSignupForm, self).__init__(*args, **kwargs)
        # Add help text to the password fields from allauth's SignupForm
        password_help_text = mark_safe(
            "<ul class='list-unstyled text-muted small ms-3'>"
            "<li>Kata sandi Anda harus mengandung setidaknya 8 karakter.</li>"
            "<li>Tidak boleh sama dengan info pribadi Anda (nama, email, dll).</li>"
            "<li>Tidak boleh kata sandi yang umum digunakan.</li>"
            "<li>Tidak boleh hanya berisi angka.</li>"
            "</ul>"
        )
        self.fields['password1'].help_text = password_help_text
        # Ensure Bootstrap classes are applied
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname')
        if nickname and CustomUser.objects.filter(nickname__iexact=nickname).exists():
            raise forms.ValidationError("Nama panggilan sudah dipakai.")
        return nickname

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            return email

        typo_domains = {
            'gmai.com': 'gmail.com',
            'gmal.com': 'gmail.com',
            'gmail.om': 'gmail.com',
            'gmail.cm': 'gmail.com',
            'gmail.co': 'gmail.com',
            'yaho.com': 'yahoo.com',
            'hotmail.co': 'hotmail.com',
        }

        try:
            domain = email.split('@')[1].lower()
            if domain in typo_domains:
                corrected_domain = typo_domains[domain]
                raise forms.ValidationError(
                    f"Domain email salah. Apakah yang Anda maksud '@{corrected_domain}'? Mohon periksa kembali email Anda."
                )
        # ini kalau tidak ada simbol @
        except IndexError:
            raise forms.ValidationError("Masukkan alamat email yang valid.")

        # Buat cek email udh dipake di akun laen ato engga
        if EmailAddress.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Alamat email ini sudah terdaftar. Silakan gunakan email lain."
            )
        return email
    
    def clean_profile_image(self):
        image = self.cleaned_data.get('profile_image', False)
        if image:
            # Limit to 2MB
            if image.size > 2 * 1024 * 1024:
                raise ValidationError("Ukuran gambar tidak boleh melebihi 2MB.")
        return image

    def save(self, request):
        # Let allauth create the user (email & password)
        user = super().save(request)

        """"
        # Now save our extra fields
        user.nickname      = self.cleaned_data['nickname']
        user.real_name     = self.cleaned_data['real_name']
        if self.cleaned_data.get('profile_image'):
            user.profile_image = self.cleaned_data['profile_image']
        user.save()
        """

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
    nickname  = forms.CharField(
        required=True, 
        max_length=100,
        label="Nama Panggilan",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    real_name = forms.CharField(
        required=True, 
        max_length=100,
        label="Nama Lengkap",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        label="Alamat Email",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('nickname', 'real_name', 'email')
        help_texts = {
            'password2': 'Masukkan kata sandi yang sama seperti di atas, untuk verifikasi.',
        }

    def __init__(self, *args, **kwargs):
        super(IPAccountCreationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].help_text = mark_safe(
            "<ul class='list-unstyled text-muted small ms-3'>"
            "<li>Kata sandi harus mengandung setidaknya 8 karakter.</li>"
            "<li>Tidak boleh kata sandi yang umum digunakan.</li>"
            "<li>Tidak boleh hanya berisi angka.</li>"
            "</ul>"
        )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
             raise forms.ValidationError("Alamat email wajib diisi.")
        email = email.lower()

        typo_domains = {
            'gmai.com': 'gmail.com',
            'gmal.com': 'gmail.com',
            'gmail.om': 'gmail.com',
            'gmail.cm': 'gmail.com',
            'gmail.co': 'gmail.com',
            'yaho.com': 'yahoo.com',
            'hotmail.co': 'hotmail.com',
        }
        
        try:
            domain = email.split('@')[1]
            if domain in typo_domains:
                raise forms.ValidationError(
                    f"Domain email salah. Apakah maksud Anda '@{typo_domains[domain]}'? Mohon periksa kembali."
                )
        except IndexError:
            raise forms.ValidationError("Masukkan alamat email yang valid.")

        if EmailAddress.objects.filter(email__iexact=email).exists() or \
           CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Alamat email ini sudah terdaftar.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        
        user.nickname = self.cleaned_data.get('nickname')
        user.real_name = self.cleaned_data.get('real_name')

        # Set role and generate username
        user.role = 'ip'
        user.username = generate_unique_username(8)
        
        if commit:
            user.save()
            if EmailAddress.objects.filter(user=user, email=user.email).count() == 0:
                 EmailAddress.objects.create(
                     user=user,
                     email=user.email,
                     primary=True,
                     verified=True
                 )
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
        help_texts = {
            'profile_image': "Ukuran file maksimal 2MB. Format yang disarankan: JPG, PNG."
        }

    def clean_nickname(self):
        nick = self.cleaned_data.get("nickname")
        qs   = CustomUser.objects.filter(nickname__iexact=nick).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Nama panggilan sudah dipakai.")
        return nick
    
    def clean_profile_image(self):
        image = self.cleaned_data.get('profile_image', False)
        if image:
            # Limit to 2MB
            if image.size > 2 * 1024 * 1024:
                raise ValidationError("Ukuran gambar tidak boleh melebihi 2MB.")
        return image

# Buat nambah help text di change password
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(CustomPasswordChangeForm, self).__init__(*args, **kwargs)
        # Add help text for the new password field
        self.fields['new_password1'].help_text = mark_safe(
            "<ul class='list-unstyled text-muted small ms-3'>"
            "<li>Kata sandi Anda harus mengandung setidaknya 8 karakter.</li>"
            "<li>Tidak boleh sama dengan info pribadi Anda.</li>"
            "<li>Tidak boleh kata sandi yang umum digunakan.</li>"
            "<li>Tidak boleh hanya berisi angka.</li>"
            "</ul>"
        )
        # Apply Bootstrap styling to all fields
        self.fields['old_password'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control'})

# Buat masukin initial rating yang manual (data atlet blom ada)
class ManualIPOpinionForm(forms.ModelForm):
    class Meta:
        model = IPRatingOpinion
        fields = ['athlete_identifier', 'opinion_rating']


