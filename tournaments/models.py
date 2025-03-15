from django.db import models
from accounts.models import AthleteProfile, CustomUser

# Create your models here.

# Model database Turney
class Tournament(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    # Ini field buat reference siapa yg bikin (IP account yg mana)
    host = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'role': 'ip'}
    )
    player_limit = models.IntegerField(choices=[(8, '8 players'), (16, '16 players')], default=8)
    participants = models.ManyToManyField(AthleteProfile, related_name='tournaments', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Nanti bisa ditambah desc laen kyk lokasi dll

    def __str__(self):
        return self.name

# Model database pertandingan
class Match(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    athlete1 = models.ForeignKey(AthleteProfile, on_delete=models.CASCADE, related_name='matches_as_athlete1')
    athlete2 = models.ForeignKey(AthleteProfile, on_delete=models.CASCADE, related_name='matches_as_athlete2')
    score1 = models.IntegerField()
    score2 = models.IntegerField()
    round = models.IntegerField(default=1)  # Buat ronde turnamen (1 = first round, 2 = quarterfinals, etc.)
    match_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Round {self.round}: {self.athlete1.user.username} vs {self.athlete2.user.username}"