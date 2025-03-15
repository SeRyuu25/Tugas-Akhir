from django.contrib import admin
from django.contrib.admin import AdminSite
from accounts.models import CustomUser, AthleteProfile, IPRatingOpinion
from tournaments.models import Tournament, Match
from ratings.models import RatingHistory
from accounts.admin import CustomUserAdmin

class MyAdminSite(AdminSite):
    site_header = 'My Custom Admin Dashboard'
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
my_admin_site.register(Tournament)
my_admin_site.register(Match)
my_admin_site.register(RatingHistory)
