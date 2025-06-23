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
    # Get the search query from the URL's GET parameters (e.g., /?q=Ryu)
    search_query = request.GET.get('q', '')

    # Start with the base queryset of all finalized athletes
    athlete_list = AthleteProfile.objects.filter(initial_rating_finalized=True)

    # If a search query exists, filter the queryset by nickname
    if search_query:
        athlete_list = athlete_list.filter(
            Q(user__nickname__icontains=search_query)
        )

    # Order the final list by rating, from highest to lowest
    athlete_list = athlete_list.order_by('-current_rating')

    # Set up the Paginator
    paginator = Paginator(athlete_list, 10) # Show 10 athletes per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Prepare the context to pass to the template
    context = {
        'page_obj': page_obj,          # The paginated object containing athletes for the current page
        'search_query': search_query,  # The current search query to display in the search box
    }
    return render(request, 'dashboard/athlete_ranking.html', context)
