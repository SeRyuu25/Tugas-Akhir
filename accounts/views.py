from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Avg
from .forms import AthleteAccountCreationForm, IPAccountCreationForm, IPRatingOpinionForm, ManualIPOpinionForm, CustomUserUpdateForm
from tournaments.models import Tournament, Match
from accounts.models import AthleteProfile, IPRatingOpinion

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
        form = AthleteAccountCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='accounts.backends.EmailBackend')
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
        pending_athletes = AthleteProfile.objects.filter(initial_rating_finalized=False).exclude(ip_opinions__ip_account=request.user)
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

# Buat edit profile (ngasih akses edit buat akun)
@login_required
def update_profile(request):
    user = request.user
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil berhasil diubah.")
            return redirect('accounts:profile')
    else:
        form = CustomUserUpdateForm(instance=user)
    return render(request, 'accounts/update_profile.html', {'form': form})

# Buat Profile yang bisa diliat publik
def public_profile(request, athlete_id):
    athlete = get_object_or_404(AthleteProfile, id=athlete_id)
    return render(request, 'accounts/public_profile.html', {'athlete': athlete})

# Buat ngasih initial rating ke atlet (dari IP)    
@login_required
@user_passes_test(is_ip)
def rate_athlete(request, athlete_id):
    # For a registered athlete (AthleteProfile), allow the IP to submit an opinion.
    athlete = get_object_or_404(AthleteProfile, id=athlete_id)
    if IPRatingOpinion.objects.filter(ip_account=request.user, athlete=athlete).exists():
        messages.error(request, "Anda sudah memberikan rating untuk atlet ini.")
        return redirect('accounts:profile')
    if request.method == 'POST':
        form = IPRatingOpinionForm(request.POST)
        if form.is_valid():
            opinion = form.save(commit=False)
            opinion.ip_account = request.user
            opinion.athlete = athlete  # link the opinion
            opinion.athlete_identifier = athlete.user.username  # auto-fill identifier
            opinion.save()
            messages.success(request, "Rating berhasil disimpan.")
            # Check if we have 3 or more opinions now
            total_opinions = IPRatingOpinion.objects.filter(athlete=athlete).count()
            # Ini kalo buat automatic finalized
            # if total_opinions >= 3 and not athlete.initial_rating_finalized:
            #     finalize_initial_rating(athlete)
            #     messages.info(request, f"Athlete {athlete.user.username}'s rating has been auto-finalized.")
            return redirect('accounts:profile')
    else:
        form = IPRatingOpinionForm(initial={'athlete_identifier': athlete.user.username})
    return render(request, 'accounts/rate_athlete.html', {'form': form, 'athlete': athlete})

@login_required
@user_passes_test(is_ip)
def create_manual_rating(request):
    if request.method == 'POST':
        form = ManualIPOpinionForm(request.POST)
        if form.is_valid():
            opinion = form.save(commit=False)
            opinion.ip_account = request.user
            opinion.save()
            messages.success(request, "Rating Anda telah disimpan.")
            return redirect('accounts:profile')
    else:
        form = ManualIPOpinionForm()
    return render(request, 'accounts/create_manual_rating.html', {'form': form})


def finalize_initial_rating(athlete):
    """
    Averages all IP opinions linked to this athlete, updates athlete's current_rating,
    and sets initial_rating_finalized=True.
    Returns a message describing the result.
    """
    # Get all opinions referencing this athlete
    opinions = athlete.ip_opinions.all()
    if not opinions.exists():
        return "Belum ada yang memberikan rating untuk atlet ini."
    
    # Calculate average rating from the 'opinion_rating' field
    avg_rating = opinions.aggregate(Avg('opinion_rating'))['opinion_rating__avg']
    if avg_rating is None:
        return "Tidak bisa menentukan rating rata-rata."
    
    # Update athlete's current_rating and mark as finalized
    athlete.current_rating = round(avg_rating)
    athlete.initial_rating_finalized = True
    athlete.save()
    
    return f"Finalisasi rating awal pada nilai {athlete.current_rating}."

# Buat admin profile -> ngasih list yg blom finalized
@login_required
@user_passes_test(is_admin)
def admin_finalize_ratings(request):
    # Get all AthleteProfile objects that have not been finalized
    athletes = AthleteProfile.objects.filter(initial_rating_finalized=False)
    context = {
        'athletes': athletes,
    }
    return render(request, 'accounts/admin_finalize_ratings.html', context)

@login_required
@user_passes_test(is_admin)
def finalize_rating_admin(request, athlete_id):
    athlete = get_object_or_404(AthleteProfile, id=athlete_id, initial_rating_finalized=False)
    # Get the average of all IP opinions linked to this athlete
    opinions = athlete.ip_opinions.all()
    if opinions.exists():
        avg_rating = opinions.aggregate(Avg('opinion_rating'))['opinion_rating__avg']
        athlete.current_rating = round(avg_rating)
        athlete.initial_rating_finalized = True
        athlete.save()
        messages.success(request, f"Rating awal {athlete.user.nickname} berhasil difinalisasi dengan rating {athlete.current_rating}.")
    else:
        messages.error(request, "Belum ada yang memberikan rating untuk atlet ini.")
    return redirect('accounts:admin_finalize_ratings')