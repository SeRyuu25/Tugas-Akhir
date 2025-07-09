from django.db import models
from accounts.models import AthleteProfile, CustomUser
import math

# Create your models here.

# Model database Turney
class Tournament(models.Model):
    TOURNAMENT_TYPE_CHOICES = [
        ('knockout', 'Sistem Gugur'),
        ('pool', 'Sistem Pool'),
    ]
    tournament_type = models.CharField(
        max_length=10, 
        choices=TOURNAMENT_TYPE_CHOICES, 
        default='knockout',
        verbose_name="Tipe Turnamen"
    )
    PLAYER_LIMIT_CHOICES = [
        (8, '8 pemain (Sistem Gugur)'),
        (12, '12 pemain (Sistem Pool)'),
        (16, '16 pemain (Sistem Gugur)'),
        (24, '24 pemain (Sistem Pool)'),
    ]
    player_limit = models.IntegerField(choices=PLAYER_LIMIT_CHOICES, default=8)
    
    name       = models.CharField(max_length=100)
    start_date = models.DateField()
    # Ini field buat reference siapa yg bikin (IP account yg mana)
    host = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'role': 'ip'}
    )
    participants = models.ManyToManyField(AthleteProfile, related_name='tournaments', blank=True)
    stage = models.CharField(max_length=10, choices=[('pool', 'Babak Pool'), ('knockout', 'Babak Gugur')], null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    is_finished  = models.BooleanField(default=False)
    # Nanti bisa ditambah desc laen kyk lokasi dll

    def get_final_round_number(self):
        """Calculates the final round number for a knockout tournament."""
        if self.player_limit > 0 and self.tournament_type == 'knockout':
            return int(math.log2(self.player_limit))
        if self.player_limit > 0 and self.tournament_type == 'pool':
            num_pools = self.player_limit / 3
            return int(math.log2(num_pools))
        return None

    def __str__(self):
        return self.name

# Model database Pool Turney
class TournamentPool(models.Model):
    tournament = models.ForeignKey('Tournament', on_delete=models.CASCADE, related_name='pools')
    name = models.CharField(max_length=100)  # e.g., "Pool A", "Pool 1"
    participants = models.ManyToManyField(AthleteProfile, related_name='tournament_pools')

    def __str__(self):
        return f"{self.tournament.name} - {self.name}"
    
    class Meta:
        verbose_name = "Tournament Pool"
        verbose_name_plural = "Tournament Pools"

# Model database pertandingan
class Match(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    athlete1   = models.ForeignKey(AthleteProfile, on_delete=models.CASCADE, related_name='matches_as_athlete1')
    athlete2   = models.ForeignKey(AthleteProfile, on_delete=models.CASCADE, related_name='matches_as_athlete2')

    round = models.PositiveIntegerField(null=True, blank=True)  # Buat ronde turnamen knockout / sistem gugur (1 = first round, 2 = quarterfinals, etc.)
    pool = models.ForeignKey(     # Buat turnamen pool
        TournamentPool, 
        on_delete=models.CASCADE, 
        related_name='matches', 
        null=True,
        blank=True
    )

    set1_p1 = models.PositiveIntegerField(null=True, blank=True)
    set1_p2 = models.PositiveIntegerField(null=True, blank=True)
    set2_p1 = models.PositiveIntegerField(null=True, blank=True)
    set2_p2 = models.PositiveIntegerField(null=True, blank=True)
    set3_p1 = models.PositiveIntegerField(null=True, blank=True)
    set3_p2 = models.PositiveIntegerField(null=True, blank=True)
    set4_p1 = models.PositiveIntegerField(null=True, blank=True)
    set4_p2 = models.PositiveIntegerField(null=True, blank=True)
    set5_p1 = models.PositiveIntegerField(null=True, blank=True)
    set5_p2 = models.PositiveIntegerField(null=True, blank=True)
    
    match_date = models.DateTimeField(auto_now_add=True)

    @property
    def context_label(self):
        if self.round:
            # For pool tournaments, the number of "players" in the knockout stage is the number of pools
            knockout_participants = self.tournament.pools.count() if self.tournament.tournament_type == 'pool' else self.tournament.player_limit
            return round_label(self.round, knockout_participants)
        elif self.pool:
            return self.pool.name
        return "N/A"

    # Hitung total set yg dimenangkan pemain (untuk ngecek seorang pemain udah menang berapa)
    def total_sets_won(self, athlete):
        win_count = 0
        for p1, p2 in [(self.set1_p1, self.set1_p2),
                     (self.set2_p1, self.set2_p2),
                     (self.set3_p1, self.set3_p2),
                     (self.set4_p1, self.set4_p2),
                     (self.set5_p1, self.set5_p2)]:
            if p1 is None or p2 is None:
                continue
            p1_wins_set = (p1 >= 11 and p1 >= p2 + 2)
            p2_wins_set = (p2 >= 11 and p2 >= p1 + 2)

            if athlete == self.athlete1 and p1_wins_set:
                win_count += 1
            elif athlete == self.athlete2 and p2_wins_set:
                win_count += 1
        return win_count

    # Buat return pemain yg menang 3 set duluan
    def winner(self):
        if self.total_sets_won(self.athlete1) >= 3:
            return self.athlete1
        if self.total_sets_won(self.athlete2) >= 3:
            return self.athlete2
        return None

    # Buat return jumlah skor yg didapat seorang pemain di 1 pertandingan
    def get_points_for_athlete(self, athlete):
        points_scored = 0
        is_athlete1 = (athlete == self.athlete1)

        all_sets = [
            (self.set1_p1, self.set1_p2),
            (self.set2_p1, self.set2_p2),
            (self.set3_p1, self.set3_p2),
            (self.set4_p1, self.set4_p2),
            (self.set5_p1, self.set5_p2)
        ]

        for p1_score, p2_score in all_sets:
            if p1_score is not None and p2_score is not None:
                if is_athlete1:
                    points_scored += p1_score
                else:
                    points_scored += p2_score
        return points_scored

    def __str__(self):
        return f"{self.tournament.name} - {self.context_label}: {self.athlete1.user.nickname} vs {self.athlete2.user.nickname}"
    
# Buat ngasih label ke html page turnamen detail
def round_label(round_number, player_count):
    total_rounds = int(math.log2(player_count)) if player_count > 0 else 0
    
    if round_number == total_rounds:
        return "Final"
    if round_number == total_rounds - 1:
        return "Semifinal"
    
    # Buat yang Babak X Besar
    num_players_in_round = 2 ** (total_rounds - round_number + 1)
    return f"Babak {num_players_in_round} Besar"
