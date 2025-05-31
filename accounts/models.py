from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

# Create your models here.

# Custom User Manager -> buat pas bikin akun (antara yg biasa & yg superadmin)
class CustomUserManager(BaseUserManager):
    # Bikin akun biasa
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        if email: # Normalize email if provided
            email = self.normalize_email(email)
        
        extra_fields.setdefault('role', 'atlet') 
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    # Buat bikin superuser / admin (biar rolenya admin)
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('role') != 'admin':
            raise ValueError('Superuser must have role of "admin".')

        return self.create_user(username, email, password, **extra_fields)

# Buat database general user (semua user)
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('ip', 'Instruktur Pertandingan'),
        ('atlet', 'Atlet'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='atlet')
    profile_image = models.ImageField(
        upload_to='profile_images/', 
        blank=True, 
        null=True
    )
    real_name = models.CharField(max_length=100, blank=False, null=False, default="Temp real name")
    nickname  = models.CharField(max_length=100, blank=False, null=False, default="Temp nickname")
    ptm       = models.CharField("Nama PTM", max_length=100, blank=True)

    # Buat ganti email, temporary check
    pending_email = models.EmailField(null=True, blank=True, unique=False)
    pending_email_requested_at = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.nickname} - {self.get_role_display()} ({self.username})"

# Buat database Atlet-related
class AthleteProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="athlete_profile")
    previous_divisi  = models.CharField("Divisi Sebelumnya", max_length=100, blank=True)
    current_rating = models.IntegerField(default=1000) # Starting ELO rating sementara
    initial_rating_finalized = models.BooleanField(default=False)
    # Nambahin atribut tentang atlet nanti di sini

    def __str__(self):
        return f"Profile Atlet - {self.user.nickname} ({self.user.username})"

# Buat database referensi atlet pas daftar
class AthleteAccountReference(models.Model):
    nickname       = models.CharField(max_length=100)
    ptm            = models.CharField("Nama PTM", max_length=100)
    divisi         = models.CharField("Divisi Sebelumnya", max_length=100)
    sudah_ada_akun = models.BooleanField(default=False)

    class Meta:
        unique_together = (("nickname","ptm"),)
        verbose_name = "Referensi Akun Atlet"
        verbose_name_plural = "Referensi Akun Atlet"

    def __str__(self):
        status = "Terpakai" if self.sudah_ada_akun else "Belum Terpakai"
        return f"{self.nickname} @ {self.ptm} — {self.divisi} ({status})"

# Buat database yang nyimpen initial rating dari IP untuk atlet tertentu
class IPRatingOpinion(models.Model):
    ip_account = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'ip'},
        related_name='rating_opinions'
    )
    # A general identifier (e.g., athlete's name or email) for the athlete
    athlete_identifier = models.CharField(max_length=255)
    # Optional link if the athlete is registered
    athlete = models.ForeignKey(
        AthleteProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='ip_opinions'
    )
    opinion_rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ip_account.nickname} ({self.ip_account.username}) -> {self.athlete_identifier}: {self.opinion_rating}"
    
    class Meta:
        # When an opinion is linked to a registered athlete, the combination of ip_account and athlete must be unique.
        unique_together = (('ip_account', 'athlete'),)