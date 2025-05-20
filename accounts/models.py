from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

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
        return f"Profile Atlet untuk {self.user.nickname} ({self.user.username})"

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