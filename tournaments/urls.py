from django.urls import path
from . import views

app_name = 'tournaments'

urlpatterns = [
    path('list/', views.tournament_list, name='tournament_list'),
    path('create/', views.create_tournament, name='create'),
    path('<int:tournament_id>/', views.tournament_detail, name='tournament_detail'),
    path('<int:tournament_id>/register/', views.register_for_tournament, name='register_for_tournament'),
    path('<int:tournament_id>/record/', views.record_match, name='record_match'),
]
