from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import TournamentForm
from .models import Tournament, Match
from accounts.models import AthleteProfile
from ratings.models import RatingHistory
from ratings.elo import process_match
import random

# Create your views here.

# View buat ngasih liat list tournament
def tournament_list(request):
    tournaments = Tournament.objects.order_by('-created_at')
    return render(request, 'tournaments/tournament_list.html', {
        'tournaments': tournaments
    })

# Func buat check IP / admin
def is_ip_or_admin(user):
    return user.is_authenticated and (user.role == 'ip' or user.is_superuser or user.role == 'admin')

# View buat bikin turnament baru (oleh IP)
@login_required
@user_passes_test(is_ip_or_admin)
def create_tournament(request):
    if request.method == 'POST':
        form = TournamentForm(request.POST)
        if form.is_valid():
            tournament = form.save(commit=False)
            tournament.host = request.user
            tournament.save()
            messages.success(request, "Tournament created successfully.")
            return redirect('tournaments:tournament_detail', tournament_id=tournament.id)
        else:
            messages.error(request, "There was an error creating the tournament.")
    else:
        form = TournamentForm()
    return render(request, 'tournaments/create_tournament.html', {'form': form})

# View buat liat detail turnament
def tournament_detail(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    # Buat pengelompokan pertandingan berdasarkan ronde / round (e.g., create a dictionary {round_number: [match, ...]})
    rounds = {}
    for match in tournament.matches.all().order_by('round'):
        rounds.setdefault(match.round, []).append(match)
    return render(request, 'tournaments/tournament_detail.html', {'tournament': tournament, 'rounds': rounds})

# View kalo ada atlet yang daftar ke suatu upcoming turney
@login_required
def register_for_tournament(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    # check role, takutnya ada yg bukan atlet tapi nyoba register
    if request.user.role != 'atlet':
        messages.error(request, "Only athlete accounts can register for tournaments.")
        return redirect('tournaments:tournament_detail', tournament_id=tournament.id)
    
    athlete_profile = request.user.athlete_profile

    if tournament.participants.count() >= tournament.player_limit:
        messages.error(request, "Tournament registration is closed because the quota is met.")
        return redirect('tournaments:tournament_detail', tournament_id=tournament.id)

    if athlete_profile in tournament.participants.all():
        messages.info(request, "You are already registered for this tournament.")
    else:
        tournament.participants.add(athlete_profile)
        messages.success(request, "You have successfully registered for the tournament.")

        # Kalo atlet yg register udh full, otomatis bikin pairing ronde pertama
        if tournament.participants.count() == tournament.player_limit:
            result_message = create_first_round_matches(tournament)
            messages.info(request, result_message)

    return redirect('tournaments:tournament_detail', tournament_id=tournament.id)

# Func buat automate bikin first round match (pairingnya) --> sementara pairing masih random
def create_first_round_matches(tournament):
    # Check if there are enough participants
    if tournament.participants.count() < tournament.player_limit:
        return "Not enough participants registered to create first round matches."
    
    # Check if round 1 matches already exist
    if tournament.matches.filter(round=1).exists():
        return "First round matches have already been created."
    
    participants = list(tournament.participants.all())
    random.shuffle(participants)
    num_matches = tournament.player_limit // 2
    for i in range(num_matches):
        athlete1 = participants[2 * i]
        athlete2 = participants[2 * i + 1]
        # Buat bikin pertandingan (match) ronde 1. Skor dianggap 0 dulu
        Match.objects.create(
            tournament=tournament,
            athlete1=athlete1,
            athlete2=athlete2,
            score1=0,
            score2=0,
            round=1
        )
    return "First round matches created successfully."

# View buat nyatet pertandingan & pergantian rating
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