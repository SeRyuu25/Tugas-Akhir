from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import AthleteProfile
from allauth.account.signals import email_confirmed
from allauth.account.models import EmailAddress


# File buat automate pembuatan profile atlet
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_athlete_profile(sender, instance, created, **kwargs):
    # Cuma bikin AthleteProfile pas ada user yg baru dibuat & rolenya atlet
    if created and instance.role == 'atlet':
        AthleteProfile.objects.create(user=instance)

# Buat ngasih sinyal pas ada yg ganti email & udh verif
@receiver(email_confirmed)
def handle_verified_email(sender, request, email_address, **kwargs):
    user = email_address.user

    # Only proceed if this matches the pending change
    if user.pending_email == email_address.email:
        # Grab the old primary address
        try:
            old_address = EmailAddress.objects.get(user=user, primary=True)
        except EmailAddress.DoesNotExist:
            old_address = None

        # Swap the User.email and make the new one primary
        user.email = email_address.email
        user.pending_email = None
        user.save()

        email_address.set_as_primary()

        # Clean up the old record
        if old_address and old_address != email_address:
            old_address.delete()