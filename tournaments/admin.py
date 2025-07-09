from django import forms
from django.contrib import admin, messages
from .models import Tournament, Match
from .views import get_pool_winner
import random

# Register your models here.

# Aksi untuk admin -- untuk manual trigger membuat bagian gugur saat selesai pool
@admin.action(description="Mulai Babak Gugur untuk Turnamen Pool Selesai")
def start_knockout_stage(modeladmin, request, queryset):
    updated_count = 0
    for tournament in queryset:
        # Action only runs on finished POOL tournaments
        if tournament.tournament_type == 'pool' and tournament.is_finished:
            # 1. Reset tournament status
            tournament.is_finished = False
            tournament.stage = 'pool'
            tournament.save()

            # 2. Generate the knockout stage
            pools = tournament.pools.all()
            if not pools.exists() or not all(get_pool_winner(p) for p in pools):
                modeladmin.message_user(request, f"Gagal memulai babak gugur untuk '{tournament.name}': Tidak semua pool memiliki pemenang.", messages.ERROR)
                continue

            winners = [get_pool_winner(pool) for pool in pools]
            random.shuffle(winners)
            
            # Delete any old knockout matches to be safe
            Match.objects.filter(tournament=tournament, pool__isnull=True).delete()
            
            # Create first knockout round
            for i in range(0, len(winners), 2):
                if i + 1 < len(winners):
                    Match.objects.create(
                        tournament=tournament,
                        athlete1=winners[i],
                        athlete2=winners[i+1],
                        round=1
                    )
            
            # 3. Finalize the stage change
            tournament.stage = 'knockout'
            tournament.save()
            updated_count += 1
    
    if updated_count > 0:
        modeladmin.message_user(request, f"Berhasil memulai babak gugur untuk {updated_count} turnamen.", messages.SUCCESS)

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
    
    list_display = ('name', 'tournament_type', 'stage', 'player_limit', 'start_date', 'is_finished')
    list_filter = ('tournament_type', 'stage', 'is_finished', 'start_date')
    
    filter_horizontal = ('participants',)

    actions = [start_knockout_stage]