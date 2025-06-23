from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import TournamentForm, MatchForm
from .models import Tournament, Match
from accounts.models import AthleteProfile
from ratings.models import RatingHistory
from ratings.elo import process_match
import random

# Create your views here.

# View buat ngasih liat list tournament
def tournament_list(request):
    upcoming_tournaments = Tournament.objects.filter(is_finished=False).order_by('start_date')
    finished_tournaments = Tournament.objects.filter(is_finished=True).order_by('-start_date')
    return render(request, 'tournaments/tournament_list.html', {
        'upcoming_tournaments': upcoming_tournaments,
        'finished_tournaments': finished_tournaments,
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
            messages.success(request, "Turnamen berhasil dibuat.")
            return redirect('tournaments:tournament_detail', tournament_id=tournament.id)
        else:
            messages.error(request, "Terdapat error saat membuat turnamen.")
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
    first_round_exists = tournament.matches.filter(round=1).exists()
    return render(request, 'tournaments/tournament_detail.html', {
        'tournament': tournament,
        'rounds': rounds,
        'first_round_exists': first_round_exists
    })

# View kalo ada atlet yang daftar ke suatu upcoming turney
@login_required
def register_for_tournament(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    # check role, takutnya ada yg bukan atlet tapi nyoba register
    if request.user.role != 'atlet':
        messages.error(request, "Hanya akun atlet yang dapat mendaftar pada turnamen.")
        return redirect('tournaments:tournament_detail', tournament_id=tournament.id)
    
    # Buat check udh finalized initial rating ato blom
    athlete_profile = request.user.athlete_profile
    if not athlete_profile.initial_rating_finalized:
        messages.error(request, "Anda belum bisa mendaftar pada turnamen ini. Rating awal Anda belum difinalisasi oleh admin.")
        return redirect('tournaments:tournament_detail', tournament_id=tournament.id)

    if tournament.participants.count() >= tournament.player_limit:
        messages.error(request, "Pendaftaran turnamen ini sudah ditutup. (Kuota atlet terpenuhi)")
        return redirect('tournaments:tournament_detail', tournament_id=tournament.id)

    if athlete_profile in tournament.participants.all():
        messages.info(request, "Anda sudah terdaftar pada turnamen ini.")
    else:
        tournament.participants.add(athlete_profile)
        messages.success(request, "Anda berhasil mendaftar pada turnamen ini.")

    return redirect('tournaments:tournament_detail', tournament_id=tournament.id)


@login_required
@user_passes_test(is_ip_or_admin)
def start_tournament(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    # Ensure that only the tournament host (IP) can start it
    if request.user != tournament.host:
        messages.error(request, "Hanya pembuat turnamen ini yang dapat memulai turnamen.")
        return redirect('tournaments:tournament_detail', tournament_id=tournament.id)
    # Check if the tournament is full
    if tournament.participants.count() < tournament.player_limit:
        messages.error(request, "Kuota atlet belum terpenuhi.")
        return redirect('tournaments:tournament_detail', tournament_id=tournament.id)
    # Check if first round matches have already been created
    if tournament.matches.filter(round=1).exists():
        messages.error(request, "Pertandingan babak pertama sudah ada.")
        return redirect('tournaments:tournament_detail', tournament_id=tournament.id)
    
    # Generate first round matches
    result_message = create_first_round_matches(tournament)
    messages.success(request, result_message)
    return redirect('tournaments:tournament_detail', tournament_id=tournament.id)

# Func buat automate bikin first round match (pairingnya) --> sementara pairing masih random
def create_first_round_matches(tournament):
    # Check if there are enough participants
    if tournament.participants.count() < tournament.player_limit:
        return "Atlet yang mendaftar masih belum cukup untuk membuat pertandingan babak pertama."
    
    # Check if round 1 matches already exist
    if tournament.matches.filter(round=1).exists():
        return "Pertandingan babak pertama sudah ada."
    
    participants = list(tournament.participants.all())
    random.shuffle(participants)
    num_matches = tournament.player_limit // 2
    for i in range(num_matches):
        athlete1 = participants[2 * i]
        athlete2 = participants[2 * i + 1]
        # Buat bikin pertandingan (match) ronde 1.
        Match.objects.create(
            tournament=tournament,
            athlete1=athlete1,
            athlete2=athlete2,
            round=1
        )
    return "Pertandingan babak pertama berhasil dibuat."

# View buat nyatet pertandingan & pergantian rating
@login_required
@user_passes_test(is_ip_or_admin)
def record_match(request, tournament_id, match_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    match = get_object_or_404(Match, id=match_id, tournament=tournament)

    # Check if the match is already concluded to prevent edits
    if match.winner() is not None:
        messages.error(request, "Hasil pertandingan ini sudah disimpan dan tidak dapat diubah.")
        return redirect('tournaments:tournament_detail', tournament_id=tournament.id)

    if request.method == 'POST':
        # Bind the POST data to a MatchForm instance linked to our specific match
        form = MatchForm(request.POST, instance=match)

        # Check for confirmation checkbox
        if 'confirm' not in request.POST:
            messages.error(request, "Anda harus mencentang kotak konfirmasi sebelum menyimpan hasil.")
            # Re-render the form with the data the user already entered
            return render(request, 'tournaments/record_match.html', {
                'tournament': tournament,
                'match': match,
                'form': form, # Pass the form back with its data
            })

        if form.is_valid():
            # Save the form to update the match instance with the new set scores.
            # The 'match' object is now updated with the scores from the form.
            form.save()

            # Now that scores are saved, get the number of sets won for each player
            wins1 = match.total_sets_won(match.athlete1)
            wins2 = match.total_sets_won(match.athlete2)

            # Process ELO and create rating history only if the match has a winner
            if wins1 >= 3 or wins2 >= 3:
                # Store the ratings *before* they are changed
                old_rating1 = match.athlete1.current_rating
                old_rating2 = match.athlete2.current_rating

                # Calculate new ratings
                new_rating1, new_rating2 = process_match(match.athlete1, match.athlete2, wins1, wins2)

                # Update athlete profiles with their new ratings
                match.athlete1.current_rating = new_rating1
                match.athlete1.save()
                match.athlete2.current_rating = new_rating2
                match.athlete2.save()

                # Create rating history records for both players
                RatingHistory.objects.create(
                    athlete=match.athlete1,
                    match=match,
                    rating_before=old_rating1,
                    rating_after=new_rating1,
                    rating_change=new_rating1 - old_rating1
                )
                RatingHistory.objects.create(
                    athlete=match.athlete2,
                    match=match,

                    rating_before=old_rating2,
                    rating_after=new_rating2,
                    rating_change=new_rating2 - old_rating2
                )

            # After saving the match, check if this completes the round
            current_round_number = match.round
            if is_round_complete(tournament, current_round_number):
                # If the round is complete, this message will be added...
                messages.info(request, f"Semua pertandingan di ronde {current_round_number} telah selesai.")
                # ...and then this function will try to generate the next round.
                generate_next_round(tournament, current_round_number, request)

            messages.success(request, "Hasil pertandingan berhasil disimpan.")
            return redirect('tournaments:tournament_detail', tournament_id=tournament.id)
        else:
            # If the form is not valid, show the errors
            messages.error(request, "Terdapat error pada data yang dimasukkan. Mohon periksa kembali skor.")

    else: # For GET requests
        form = MatchForm(instance=match)

    return render(request, 'tournaments/record_match.html', {
        'tournament': tournament,
        'match': match,
        'form': form,
    })

# Func buat cek 1 ronde udh beres ato blom
def is_round_complete(tournament, round_number):
    """
    Check if all matches in the given round are completed.
    """
    matches = tournament.matches.filter(round=round_number)
    return all(match.winner() is not None for match in matches)

# Func buat generate ronde selanjutnya kalo 1 ronde udh beres
def generate_next_round(tournament, current_round, request):
    current_matches = tournament.matches.filter(round=current_round)
    winners = [m.winner() for m in current_matches if m.winner() is not None]

    # Check if this was the final round by seeing if there's only one winner left
    if len(winners) == 1:
        final_winner = winners[0]
        messages.success(request, f"Turnamen telah selesai. Pemenangnya adalah {final_winner.user.nickname}!")
        
        # --- Mark the tournament as finished ---
        tournament.is_finished = True
        tournament.save(update_fields=['is_finished'])
        return # Stop further processing

    # If there are no winners yet but the round is complete (e.g. invalid data), do nothing
    if not winners:
        return

    # Pair the winners for the next round
    next_round_number = current_round + 1
    # Shuffle winners to randomize pairings in the next round
    random.shuffle(winners)
    for i in range(0, len(winners), 2):
        # Ensure there's a pair to create a match
        if i + 1 < len(winners):
            athlete1 = winners[i]
            athlete2 = winners[i + 1]
            Match.objects.create(
                tournament=tournament,
                athlete1=athlete1,
                athlete2=athlete2,
                round=next_round_number
            )
    messages.info(request, f"Pertandingan ronde {next_round_number} sudah dibuat.")

# Func buat nentuin final round
def get_final_round(player_limit):
    if player_limit == 8:
        return 3  # Final round for 8 players
    elif player_limit == 16:
        return 4  # Final round for 16 players
    else:
        return 0
    
