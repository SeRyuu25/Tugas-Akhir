from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import TournamentForm, MatchForm
from .models import Tournament, Match, TournamentPool, round_label
from accounts.models import AthleteProfile
from ratings.models import RatingHistory
from ratings.elo import process_match
import random
import itertools

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
            if tournament.tournament_type == 'knockout':
                tournament.stage = 'knockout'
            else:
                tournament.stage = 'pool'
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

    # Buat pengelompokan pertandingan (rounds buat Gugur / Knockout, pools buat Pools) - bentuknya dictionary
    rounds = {}
    pools_with_matches = []
    final_results = {}
    pool_winners = []

    # Kalo turnament udh beres, display hasil ordernya reverse (dari final dulu)
    if tournament.is_finished:
        if tournament.tournament_type == 'pool':
            for match in tournament.matches.filter(pool__isnull=True).order_by('-round', 'id'):
                rounds.setdefault(match.round, []).append(match)
            all_pools = tournament.pools.all().order_by('name')
            for pool in all_pools:
                pools_with_matches.append({
                    'pool': pool, 
                    'matches': pool.matches.all().order_by('id')
                })
                winner = get_pool_winner(pool)
                if winner:
                    pool_winners.append({'pool_name': pool.name, 'winner': winner})
        else: # Buat yg sistem gugur
            for match in tournament.matches.all().order_by('-round', 'id'):
                rounds.setdefault(match.round, []).append(match)

    # Kalo belom beres, sesuai urutan (ronde 1 sampe final)
    else:
        if tournament.tournament_type == 'knockout':
            for match in tournament.matches.all().order_by('round', 'id'):
                rounds.setdefault(match.round, []).append(match)
        
        elif tournament.tournament_type == 'pool':
            all_pools = tournament.pools.all().order_by('name')
            for pool in all_pools:
                pools_with_matches.append({
                    'pool': pool, 
                    'matches': pool.matches.all().order_by('id')
                })
            if tournament.stage == 'knockout':
                for pool in all_pools:
                    winner = get_pool_winner(pool)
                    if winner:
                        pool_winners.append({'pool_name': pool.name, 'winner': winner})
                for match in tournament.matches.filter(pool__isnull=True).order_by('round', 'id'):
                    rounds.setdefault(match.round, []).append(match)

    if tournament.is_finished:
        final_round_num = tournament.get_final_round_number()
        if final_round_num:
            final_match = tournament.matches.filter(round=final_round_num).first()
            if final_match and final_match.winner():
                final_results['rank1'] = final_match.winner()
                final_results['rank2'] = final_match.athlete1 if final_match.winner() == final_match.athlete2 else final_match.athlete2

                # Find Top 4 (semifinal losers)
                semifinal_round_num = final_round_num - 1
                semifinal_matches = tournament.matches.filter(round=semifinal_round_num)
                semifinal_losers = []
                for match in semifinal_matches:
                    if match.winner():
                        loser = match.athlete1 if match.winner() == match.athlete2 else match.athlete2
                        semifinal_losers.append(loser)
                final_results['top4'] = semifinal_losers
            
    first_round_exists = tournament.matches.filter(round=1).exists() or tournament.matches.filter(pool__isnull=False).exists()
    
    return render(request, 'tournaments/tournament_detail.html', {
        'tournament': tournament,
        'rounds': rounds,
        'pools_with_matches': pools_with_matches,
        'first_round_exists': first_round_exists,
        'final_results': final_results,
        'pool_winners': pool_winners,
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
    if tournament.tournament_type == 'knockout':
        result_message = create_first_round_matches(tournament)
        messages.success(request, result_message)
    elif tournament.tournament_type == 'pool':
        result_message = create_pools_and_matches(tournament)
        messages.success(request, result_message)
    else:
        # Fallback buat jaga-jaga
        messages.error(request, "Tipe turnamen tidak diketahui.")

    return redirect('tournaments:tournament_detail', tournament_id=tournament.id)

# Func buat automate bikin first round match untuk sistem Gugur / Knockout (pairingnya) --> sementara pairing masih random
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

# Fungsi buat bantu bikin pool di tournament
def create_pools_and_matches(tournament):
    participants = list(tournament.participants.all())
    random.shuffle(participants)

    players_per_pool = 3 # Nanti bisa diganti kalo mau lbh banyak pemain di 1 pool
    num_pools = tournament.player_limit // players_per_pool

    for i in range(num_pools):
        pool_name = f"Pool {i + 1}"
        # Create the pool object
        pool = TournamentPool.objects.create(tournament=tournament, name=pool_name)
        
        # Get the slice of players for this pool
        start_index = i * players_per_pool
        end_index = start_index + players_per_pool
        pool_participants = participants[start_index:end_index]
        
        # Add participants to the pool's ManyToManyField
        pool.participants.add(*pool_participants)

        # Generate round-robin matches for this pool
        for athlete1, athlete2 in itertools.combinations(pool_participants, 2):
            Match.objects.create(
                tournament=tournament,
                pool=pool, # Link the match to the pool
                athlete1=athlete1,
                athlete2=athlete2,
                # 'round' field is left null for pool matches
            )
    
    return f"{num_pools} pool berhasil dibuat dengan pertandingan round-robin."

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
            if tournament.tournament_type == 'pool' and tournament.stage == 'pool':
                if is_pool_complete(match.pool):
                    messages.info(request, f"Semua pertandingan di {match.pool.name} telah selesai.")
                    if are_all_pools_finished(tournament):
                        # Transition to knockout stage
                        tournament.stage = 'knockout'
                        tournament.save(update_fields=['stage'])
                        generate_knockout_stage_for_pools(tournament, request)
            elif match.round:
                if is_round_complete(tournament, match.round):
                    round_name = match.context_label
                    messages.info(request, f"Semua pertandingan di babak {round_name} telah selesai.")
                    generate_next_round(tournament, match.round, request)

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

# Buat pindah dari pool ke knockout (ambil pemenang pool trus generate ronde 1 knockout)
def generate_knockout_stage_for_pools(tournament, request):
    pools = tournament.pools.all().order_by('name')
    winners = [get_pool_winner(pool) for pool in pools if get_pool_winner(pool) is not None]

    if not winners or len(winners) != tournament.pools.count():
        messages.error(request, "Gagal mengumpulkan pemenang pool untuk memulai babak gugur.")
        return

    random.shuffle(winners)

    knockout_start_round = 1

    for i in range(0, len(winners), 2):
        if i + 1 < len(winners):
            Match.objects.create(
                tournament=tournament,
                athlete1=winners[i],
                athlete2=winners[i+1],
                round=knockout_start_round
            )
    messages.success(request, f"Babak Gugur (Pool) telah dibuat dengan {len(winners)} pemenang pool.")

# Func buat cek 1 ronde udh beres ato blom
def is_round_complete(tournament, round_number):
    """
    Check if all matches in the given round are completed.
    """
    matches = tournament.matches.filter(round=round_number)
    if not matches.exists(): return False
    return all(match.winner() is not None for match in matches)

# Fungsi buat cek apakah semua pertandingan di 1 pool sudah beres ato blom
def is_pool_complete(pool):
    """Checks if all matches in a given pool have a winner."""
    # A pool is complete if the number of matches equals the number of matches with a winner.
    return pool.matches.count() > 0 and pool.matches.count() == len([m for m in pool.matches.all() if m.winner() is not None])

# Fungsi buat nentuin yg menang di 1 pool
def get_pool_winner(pool):
    """
    Determines the winner of a completed 3-person pool using a multi-step tie-breaker.
    1. Most Match Wins -> 2. Set Ratio -> 3. Point Ratio
    """
    if not is_pool_complete(pool):
        return None

    participants = list(pool.participants.all())
    matches_in_pool = pool.matches.all()

    # Kriteria 1 : Paling banyak menang di 1 pool itu
    win_counts = {p: 0 for p in participants}
    for match in matches_in_pool:
        winner = match.winner()
        if winner:
            win_counts[winner] += 1
    
    max_wins = max(win_counts.values()) if win_counts else 0
    tied_players = [p for p, w in win_counts.items() if w == max_wins]

    if len(tied_players) == 1:
        return tied_players[0]
    
    # Kriteria 2 : Perbandingan set menang / kalah (selisih set)
    set_ratios = {}
    for player in tied_players:
        sets_won = sum(match.total_sets_won(player) for match in matches_in_pool)
        sets_lost = sum(
            match.total_sets_won(match.athlete1 if player == match.athlete2 else match.athlete2) 
            for match in matches_in_pool
        )
        set_ratios[player] = sets_won / sets_lost if sets_lost > 0 else float('inf')

    max_set_ratio = max(set_ratios.values())
    set_ratio_winners = [p for p, r in set_ratios.items() if r == max_set_ratio]

    if len(set_ratio_winners) == 1:
        return set_ratio_winners[0]

    # Kriteria 3 : Perbandingan skor poin menang / kalah (selisih skor poin)
    point_ratios = {}
    for player in set_ratio_winners:
        points_won = sum(match.get_points_for_athlete(player) for match in matches_in_pool)
        points_lost = sum(
            match.get_points_for_athlete(match.athlete1 if player == match.athlete2 else match.athlete2) 
            for match in matches_in_pool
        )
        point_ratios[player] = points_won / points_lost if points_lost > 0 else float('inf')

    max_point_ratio = max(point_ratios.values())
    point_ratio_winners = [p for p, r in point_ratios.items() if r == max_point_ratio]

    if point_ratio_winners:
        # Ini untuk final sementara
        # Kalau msh 2+ pemain yg tied, dianggap yg pertama (di list) yang menang
        return point_ratio_winners[0]

    # Fallback buat jaga-jaga error
    return tied_players[0] if tied_players else None

# Fungsi buat cek apakah di pool turnament, semua pool udh beres ato blom
def are_all_pools_finished(tournament):
    """Checks if every pool in the tournament is complete."""
    # Ensure there are pools to check
    if not tournament.pools.exists():
        return False
    # Return True only if every single pool is complete
    return all(is_pool_complete(pool) for pool in tournament.pools.all())

# Func buat generate ronde selanjutnya kalo 1 ronde udh beres
def generate_next_round(tournament, current_round, request):
    current_matches = tournament.matches.filter(round=current_round)
    winners = [m.winner() for m in current_matches if m.winner() is not None]

    # Buat cek klo final round
    final_round_num = tournament.get_final_round_number()
    if current_round == final_round_num:
        if winners:
            final_winner = winners[0]
            messages.success(request, f"Turnamen telah selesai. Pemenangnya adalah {final_winner.user.nickname}!")
            tournament.is_finished = True
            tournament.save(update_fields=['is_finished'])
        return

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
    player_count = len(winners) * 2 # player count for the round that just finished
    next_round_label = round_label(next_round_number, player_count)
    messages.info(request, f"Pertandingan untuk babak {next_round_label} sudah dibuat.")

# Func buat nentuin final round
def get_final_round(player_limit):
    if player_limit == 8:
        return 3  # Final round for 8 players
    elif player_limit == 16:
        return 4  # Final round for 16 players
    else:
        return 0
    
