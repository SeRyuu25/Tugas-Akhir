from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('ip', 'Instruktur Pertandingan'),
        ('atlet', 'Atlet'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='atlet')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
