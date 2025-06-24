from django.shortcuts import render
from tournaments.models import Tournament
from accounts.models import AthleteProfile
from django.db.models import Q
from django.core.paginator import Paginator

# Create your views here.

# View buat ngasih liat home alias dashboard
def home(request):
    # Ambil list turnament yg deket (order by start_date)
    tournaments = Tournament.objects.filter(is_finished=False).order_by('start_date')[:5]
    # Ambil list top atlet (berdasarkan current_rating)
    top_athletes = AthleteProfile.objects.order_by('-current_rating')[:5]
    return render(request, 'dashboard/home.html', {
        'tournaments': tournaments,
        'top_athletes': top_athletes,
    })

# View buat ngasih liat ranking atlet
# Buat sementara di sini, nanti bisa dipindah kalo butuh
def athlete_ranking(request):
    search_query = request.GET.get('q', '')

    # First, get the complete ranked list of ALL finalized athlete IDs.
    # This list establishes the "true" rank.
    all_ranked_ids = list(AthleteProfile.objects.filter(
        initial_rating_finalized=True
    ).order_by('-current_rating').values_list('id', flat=True))

    # Start with the base queryset for filtering
    athlete_list = AthleteProfile.objects.filter(initial_rating_finalized=True)

    if search_query:
        athlete_list = athlete_list.filter(
            Q(user__nickname__icontains=search_query)
        )
    
    # Order the filtered list
    athlete_list = athlete_list.order_by('-current_rating')

    # Paginate the filtered list
    paginator = Paginator(athlete_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Now, add the true rank to each athlete on the CURRENT page
    for athlete in page_obj:
        try:
            # Find the athlete's index in the full ranked list and add 1
            athlete.true_rank = all_ranked_ids.index(athlete.id) + 1
        except ValueError:
            athlete.true_rank = "N/A"

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'dashboard/athlete_ranking.html', context)
