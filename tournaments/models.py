from django.db import models
from accounts.models import AthleteProfile, CustomUser

# Create your models here.

# Model database Turney
class Tournament(models.Model):
    name       = models.CharField(max_length=100)
    start_date = models.DateField()
    # Ini field buat reference siapa yg bikin (IP account yg mana)
    host = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'role': 'ip'}
    )
    player_limit = models.IntegerField(choices=[(8, '8 pemain'), (16, '16 pemain')], default=8)
    participants = models.ManyToManyField(AthleteProfile, related_name='tournaments', blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    is_finished  = models.BooleanField(default=False)
    # Nanti bisa ditambah desc laen kyk lokasi dll

    def __str__(self):
        return self.name

# Model database pertandingan
class Match(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    athlete1   = models.ForeignKey(AthleteProfile, on_delete=models.CASCADE, related_name='matches_as_athlete1')
    athlete2   = models.ForeignKey(AthleteProfile, on_delete=models.CASCADE, related_name='matches_as_athlete2')
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
    round      = models.IntegerField(default=1)  # Buat ronde turnamen (1 = first round, 2 = quarterfinals, etc.)
    match_date = models.DateTimeField(auto_now_add=True)

    # Hitung total set yg dimenangkan pemain (untuk tiebreaker)
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

    def __str__(self):
        return f"Ronde {self.round}: {self.athlete1.user.nickname} ({self.athlete1.user.username}) vs {self.athlete2.user.nickname} ({self.athlete2.user.username})"
    
# Buat ngasih label ke html page turnamen detail
def round_label(round_number, player_limit):
    """
    Maps the integer round to a human-readable label.
    For an 8-player tournament: 3 rounds -> R1=Round of 8, R2=Semifinal, R3=Final
    For a 16-player tournament: 4 rounds -> R1=Round of 16, R2=Round of 8, R3=Semifinal, R4=Final
    """
    if player_limit == 8:
        mapping = {
            1: "Babak 8 Besar",
            2: "Semifinal",
            3: "Final"
        }
    elif player_limit == 16:
        mapping = {
            1: "Babak 16 Besar",
            2: "Babak 8 Besar",
            3: "Semifinal",
            4: "Final"
        }
    else:
        # Fallback or a more generic approach
        mapping = {round_number: f"Ronde {round_number}"}
    
    return mapping.get(round_number, f"Ronde {round_number}")
