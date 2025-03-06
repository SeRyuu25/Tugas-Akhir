from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

# Buat database general user
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

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

# Buat database Atlet-related
class AthleteProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="athlete_profile")
    current_rating = models.IntegerField(default=1000) # Starting ELO rating sementara
    initial_rating_finalized = models.BooleanField(default=False)
    # Nambahin atribut tentang atlet nanti di sini

    def __str__(self):
        return f"Profile Atlet untuk {self.user.username}"