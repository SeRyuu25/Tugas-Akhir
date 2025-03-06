from django.urls import path
from . import views
from .views import home

app_name = 'dashboard'  # This registers the namespace (nanti buat dashboard:home dll)

urlpatterns = [
    path('', home, name='home'),
    path('ranking/', views.athlete_ranking, name='athlete_ranking'),
]
