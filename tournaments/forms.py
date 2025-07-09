from django import forms
from .models import Tournament, Match
import datetime
from django.core.exceptions import ValidationError

# Form buat bikin Turney baru
class TournamentForm(forms.ModelForm):
    class Meta:
        model   = Tournament
        fields  = ['name', 'start_date', 'tournament_type', 'player_limit']  # Nanti bisa ditambah fieldnya klo kurang
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tournament_type': forms.Select(attrs={'class': 'form-select'}),
            'player_limit': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'name': 'Nama Turnamen',
            'start_date': 'Tanggal Mulai',
            'tournament_type': 'Tipe Turnamen',
            'player_limit': 'Batas Pemain',
        }

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date and start_date < datetime.date.today():
            raise ValidationError("Tanggal Mulai harus di masa depan.")
        return start_date

class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = [
            'set1_p1','set1_p2',
            'set2_p1','set2_p2',
            'set3_p1','set3_p2',
            'set4_p1','set4_p2',
            'set5_p1','set5_p2',
        ]
        widgets = {
            f'set{i}_{side}': forms.NumberInput(attrs={'class': 'score-input', 'min': 0})
            for i in range(1,6) for side in ('p1','p2')
        }

    def clean(self):
        cleaned_data = super().clean()
        
        # Helper function to check for a plausible score
        def is_plausible_set_win(score1, score2):
            # Don't validate empty sets, only sets with scores
            if score1 is None or score2 is None:
                return True 
            
            winner = max(score1, score2)
            loser = min(score1, score2)

            # A winner must have at least 11 points. If not, it's not a completed set.
            # We don't raise an error here, because the user might be halfway through typing.
            if winner < 11:
                return False 
            
            # Normal win: score is 11, loser is 9 or less.
            if winner == 11:
                return loser <= 9
            
            # Deuce win: score is > 11, must win by exactly 2.
            return winner == loser + 2

        p1_wins = 0
        p2_wins = 0
        match_decided_at_set = None

        for i in range(1, 6):
            p1 = cleaned_data.get(f'set{i}_p1')
            p2 = cleaned_data.get(f'set{i}_p2')

            # Only validate sets that have scores entered
            if p1 is not None and p2 is not None:
                if not is_plausible_set_win(p1, p2):
                    # This score is impossible (e.g., 23-5 or 11-10)
                    raise ValidationError(f"Skor pada Set {i} ({p1}-{p2}) tidak valid. Permainan harus dimenangkan dengan skor 11 (selisih 2 poin) atau saat deuce (selisih 2 poin).")
                
                # Count wins if it's a valid set
                if (p1 >= 11 and p1 >= p2 + 2) or (p2 >= 11 and p2 >= p1 + 2):
                    if p1 > p2: p1_wins += 1
                    elif p2 > p1: p2_wins += 1
            
            # Check if the match is over
            if not match_decided_at_set and (p1_wins >= 3 or p2_wins >= 3):
                match_decided_at_set = i

        # Check for scores entered in sets after the match was already decided
        if match_decided_at_set:
            for i in range(match_decided_at_set + 1, 6):
                p1 = cleaned_data.get(f'set{i}_p1')
                p2 = cleaned_data.get(f'set{i}_p2')
                # A score is only invalid if it's greater than 0
                if (p1 or 0) > 0 or (p2 or 0) > 0:
                    raise ValidationError(
                        f"Set {i} harus kosong karena pertandingan sudah selesai di Set {match_decided_at_set}."
                    )

        return cleaned_data