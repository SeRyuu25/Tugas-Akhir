from django import forms
from django.contrib import admin
from .models import Tournament

# Register your models here.

class TournamentAdminForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = '__all__'

    # Buat validasi jumlah pemain yang didaftarkan manual oleh admin
    def clean_participants(self):
        participants = self.cleaned_data.get('participants')
        player_limit = self.cleaned_data.get('player_limit')

        if participants and player_limit and len(participants) > player_limit:
            raise forms.ValidationError(
                f"Jumlah pemain ({len(participants)}) tidak bisa melebihi jumlah maksimal pada turnament ini ({player_limit})."
            )
        
        return participants
    
# Buat pasang validasi di atas ke admin dashboardnya
class TournamentAdmin(admin.ModelAdmin):
    form = TournamentAdminForm
    
    list_display = ('name', 'tournament_type', 'player_limit', 'start_date', 'is_finished')
    list_filter = ('tournament_type', 'is_finished', 'start_date')
    
    filter_horizontal = ('participants',)