from django.urls import path
from .views import home

app_name = 'dashboard'  # This registers the namespace

urlpatterns = [
    path('', home, name='home'),
]
