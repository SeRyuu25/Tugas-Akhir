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
        return f"{self.ip_account.username} -> {self.athlete_identifier}: {self.opinion_rating}"