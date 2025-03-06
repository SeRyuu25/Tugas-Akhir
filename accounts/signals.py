from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AthleteProfile

# File buat automate pembuatan profile atlet

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_athlete_profile(sender, instance, created, **kwargs):
    # Cuma bikin AthleteProfile pas ada user yg baru dibuat & rolenya atlet
    if created and instance.role == 'atlet':
        AthleteProfile.objects.create(user=instance)