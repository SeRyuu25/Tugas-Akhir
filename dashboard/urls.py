from django.urls import path
from .views import home

app_name = 'dashboard'  # This registers the namespace (nanti buat dashboard:home dll)

urlpatterns = [
    path('', home, name='home'),
]
