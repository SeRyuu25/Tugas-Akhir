from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.sites.models import Site
from django.contrib.auth.models import Group

from allauth.account.models import EmailAddress

from accounts.models import CustomUser, AthleteProfile, IPRatingOpinion, AthleteAccountReference
from tournaments.models import Tournament, Match
from ratings.models import RatingHistory
from accounts.admin import CustomUserAdmin
from accounts.admin import AthleteAccountReferenceAdmin

class MyAdminSite(AdminSite):
    site_header = 'Tenis Meja Admin Dashboard'
    site_title = 'Custom Admin'
    index_title = 'Dashboard'

    def index(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        # Pass tournaments to the index template
        extra_context['tournaments'] = Tournament.objects.all().order_by('-created_at')
        extra_context['recent_ip_opinions'] = IPRatingOpinion.objects.order_by('-created_at')[:5]
        return super().index(request, extra_context=extra_context)

# Instantiate your custom admin site
my_admin_site = MyAdminSite(name='myadmin')

# Register your models with the custom admin site
my_admin_site.register(CustomUser, CustomUserAdmin)
my_admin_site.register(AthleteProfile)
my_admin_site.register(IPRatingOpinion)
my_admin_site.register(AthleteAccountReference, AthleteAccountReferenceAdmin)
my_admin_site.register(Tournament)
my_admin_site.register(Match)
my_admin_site.register(RatingHistory)

my_admin_site.register(Site)

my_admin_site.register(EmailAddress)