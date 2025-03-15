from django import forms
from .models import Tournament
import datetime
from django.core.exceptions import ValidationError

# Form buat bikin Turney baru
class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = ['name', 'start_date', 'player_limit']  # Nanti bisa ditambah fieldnya klo kurang
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date and start_date < datetime.date.today():
            raise ValidationError("The start date must be in the future.")
        return start_date