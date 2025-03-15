from django.db import models
from accounts.models import AthleteProfile
from tournaments.models import Match

# Create your models here.

# Model buat nyimpen history perubahan rating
class RatingHistory(models.Model):
    athlete = models.ForeignKey(AthleteProfile, on_delete=models.CASCADE, related_name='rating_history')
    match = models.ForeignKey(Match, on_delete=models.SET_NULL, null=True, blank=True)
    rating_before = models.IntegerField()
    rating_after = models.IntegerField()
    rating_change = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.athlete.user.username}: {self.rating_before} -> {self.rating_after}"