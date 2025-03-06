from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import AthleteAccountCreationForm, IPAccountCreationForm, IPRatingOpinionForm
from django.contrib.auth.decorators import login_required, user_passes_test
from tournaments.models import Tournament, Match
from accounts.models import AthleteProfile, IPRatingOpinion
from django.utils import timezone
from django.db.models import Q

# Create your views here.

# Cek akun admin ato bukan
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'admin')

# Cek akun IP ato bukan 
def is_ip(user):
    return user.is_authenticated and (user.role == 'ip' or user.is_superuser or user.role == 'admin')

# Buat registrasi akun atlet
def register(request):
    if request.method == 'POST':
        form = AthleteAccountCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Setelah registrasi, redirect ke home page
            return redirect('dashboard:home')
        else:
            # Ini sementara : buat ngasih liat error pas debugging
            print(form.errors)
    else:
        form = AthleteAccountCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

# Buat bikin akun IP oleh admin / superuser
@login_required
@user_passes_test(is_admin)
def create_ip_account(request):
    if request.method == 'POST':
        form = IPAccountCreationForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect ke admin page
            return redirect('admin:index')
    else:
        form = IPAccountCreationForm()
    return render(request, 'accounts/create_ip_account.html', {'form': form})

# Buat Profile
@login_required
def profile(request):
    user = request.user
    if user.role == 'atlet':
        # For athlete accounts: show profile data, upcoming & finished tournaments, and match records.
        athlete_profile = user.athlete_profile
        upcoming_tournaments = Tournament.objects.filter(
            participants=athlete_profile,  # use the participants relation
            start_date__gte=timezone.now()  # gte = greater than / equal
        )
        finished_tournaments = Tournament.objects.filter(
            participants=athlete_profile,
            start_date__lt=timezone.now()  # lt = less than
        )
        matches = Match.objects.filter(
            Q(athlete1=athlete_profile) | Q(athlete2=athlete_profile)
        ).order_by('-match_date')
        context = {
            'athlete_profile': athlete_profile,
            'upcoming_tournaments': upcoming_tournaments,
            'finished_tournaments': finished_tournaments,
            'matches': matches,
        }
        return render(request, 'accounts/athlete_profile.html', context)
    elif user.role == 'ip':
        # For IP accounts: show tournaments hosted by the IP, pending registered athletes, and manual opinions.
        tournaments_hosted = Tournament.objects.filter(host=user)
        pending_athletes = AthleteProfile.objects.filter(initial_rating_finalized=False)
        manual_opinions = IPRatingOpinion.objects.filter(ip_account=user, athlete__isnull=True)
        context = {
            'tournaments_hosted': tournaments_hosted,
            'pending_athletes': pending_athletes,
            'manual_opinions': manual_opinions,
        }
        return render(request, 'accounts/ip_profile.html', context)
    else:
        # For other roles (e.g. admin) you can render a default profile page.
        return render(request, 'accounts/profile.html')

# Buat Profile yang bisa diliat publik
def public_profile(request, athlete_id):
    # Retrieve the AthleteProfile for the given athlete_id
    athlete = get_object_or_404(AthleteProfile, id=athlete_id)
    return render(request, 'accounts/public_profile.html', {'athlete': athlete})

# Buat ngasih initial rating ke atlet (dari IP)    
@login_required
@user_passes_test(is_ip)
def rate_athlete(request, athlete_id):
    # For a registered athlete (AthleteProfile), allow the IP to submit an opinion.
    athlete = get_object_or_404(AthleteProfile, id=athlete_id)
    if request.method == 'POST':
        form = IPRatingOpinionForm(request.POST)
        if form.is_valid():
            opinion = form.save(commit=False)
            opinion.ip_account = request.user
            opinion.athlete = athlete  # link the opinion
            opinion.athlete_identifier = athlete.user.username  # auto-fill identifier
            opinion.save()
            return redirect('accounts:ip_profile')
    else:
        form = IPRatingOpinionForm(initial={'athlete_identifier': athlete.user.username})
    return render(request, 'accounts/rate_athlete.html', {'form': form, 'athlete': athlete})