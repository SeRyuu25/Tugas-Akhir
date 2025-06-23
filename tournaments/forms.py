from django import forms
from .models import Tournament, Match
import datetime
from django.core.exceptions import ValidationError

# Form buat bikin Turney baru
class TournamentForm(forms.ModelForm):
    class Meta:
        model   = Tournament
        fields  = ['name', 'start_date', 'player_limit']  # Nanti bisa ditambah fieldnya klo kurang
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date and start_date < datetime.date.today():
            raise ValidationError("The start date must be in the future.")
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
        cleaned = super().clean()
        wins1 = wins2 = 0
        decided = None

        # Otomatis menghitung set sampe ada yg 3 duluan
        for idx in range(1,6):
            p1 = cleaned.get(f'set{idx}_p1') or 0
            p2 = cleaned.get(f'set{idx}_p2') or 0
            if p1 > p2:
                wins1 += 1
            elif p2 > p1:
                wins2 += 1

            if wins1 == 3 or wins2 == 3:
                decided = idx
                break

        # Memastikan tidak ada skor yang aneh bila sudah ada pemenang
        if decided:
            for idx in range(decided+1, 6):
                if (cleaned.get(f'set{idx}_p1') or 0) > 0 or (cleaned.get(f'set{idx}_p2') or 0) > 0:
                    raise forms.ValidationError(
                        f"Set {idx} harus kosong atau 0 saat seorang pemain sudah menang 3 set (menang di set {decided})."
                    )
        return cleaned