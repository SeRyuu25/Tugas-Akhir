from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import TournamentForm
from .models import Tournament, Match
from accounts.models import AthleteProfile
from ratings.elo import process_match
from ratings.models import RatingHistory

# Create your views here.

def tournament_list(request):
    tournaments = Tournament.objects.order_by('-created_at')
    return render(request, 'tournaments/tournament_list.html', {
        'tournaments': tournaments
    })

def is_ip_or_admin(user):
    return user.is_authenticated and (user.role == 'ip' or user.is_superuser or user.role == 'admin')

@login_required
@user_passes_test(is_ip_or_admin)
def create_tournament(request):
    if request.method == 'POST':
        form = TournamentForm(request.POST)
        if form.is_valid():
            tournament = form.save()
            return redirect('tournaments:tournament_detail', tournament_id=tournament.id)
    else:
        form = TournamentForm()
    return render(request, 'tournaments/create_tournament.html', {'form': form})

def tournament_detail(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    # Group matches by round (e.g., create a dictionary {round_number: [match, ...]})
    rounds = {}
    for match in tournament.matches.all().order_by('round'):
        rounds.setdefault(match.round, []).append(match)
    return render(request, 'tournaments/tournament_detail.html', {'tournament': tournament, 'rounds': rounds})

def record_match(request, tournament_id):
    # Buat prototype, sementara detail pertandingan dikirim dari POST form.
    if request.method == 'POST':
        tournament = get_object_or_404(Tournament, id=tournament_id)
        athlete1_id = request.POST.get('athlete1')
        athlete2_id = request.POST.get('athlete2')
        score1 = int(request.POST.get('score1'))
        score2 = int(request.POST.get('score2'))
        
        athlete1 = get_object_or_404(AthleteProfile, id=athlete1_id)
        athlete2 = get_object_or_404(AthleteProfile, id=athlete2_id)
        
        # Pembuatan data pertandingan
        match = Match.objects.create(
            tournament=tournament,
            athlete1=athlete1,
            athlete2=athlete2,
            score1=score1,
            score2=score2,
        )
        
        # Proses perubahan ELO rating
        old_rating1 = athlete1.current_rating
        old_rating2 = athlete2.current_rating
        
        new_rating1, new_rating2 = process_match(athlete1, athlete2, score1, score2)
        
        # Update profil Atlet
        athlete1.current_rating = new_rating1
        athlete1.save()
        athlete2.current_rating = new_rating2
        athlete2.save()
        
        # Pembuatan log history rating buat kedua atlet
        RatingHistory.objects.create(
            athlete=athlete1,
            match=match,
            rating_before=old_rating1,
            rating_after=new_rating1,
            rating_change=new_rating1 - old_rating1
        )
        RatingHistory.objects.create(
            athlete=athlete2,
            match=match,
            rating_before=old_rating2,
            rating_after=new_rating2,
            rating_change=new_rating2 - old_rating2
        )
        
        return redirect('tournaments:tournament_detail', tournament_id=tournament.id)
    else:
        # For GET, render a simple form to record a match
        return render(request, 'tournaments/record_match.html', {'tournament_id': tournament_id})