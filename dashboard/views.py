from django.shortcuts import render
from tournaments.models import Tournament
from accounts.models import AthleteProfile

# Create your views here.

def home(request):
    # Ambil list turnament yg deket (order by start_date)
    tournaments = Tournament.objects.order_by('start_date')[:5]
    # Ambil list top atlet (berdasarkan current_rating)
    top_athletes = AthleteProfile.objects.order_by('-current_rating')[:5]
    return render(request, 'dashboard/home.html', {
        'tournaments': tournaments,
        'top_athletes': top_athletes,
    })

# Buat sementara di sini, nanti bisa dipindah kalo butuh
def athlete_ranking(request):
    athletes = AthleteProfile.objects.order_by('-current_rating')
    return render(request, 'dashboard/athlete_ranking.html', {
        'athletes': athletes
    })