from django.urls import path
from . import views

app_name = 'tournaments'

urlpatterns = [
    path('<int:tournament_id>/', views.tournament_detail, name='tournament_detail'),
    path('<int:tournament_id>/record/', views.record_match, name='record_match'),
]
