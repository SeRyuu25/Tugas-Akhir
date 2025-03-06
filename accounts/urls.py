from django.urls import path
from django.contrib.auth import views as auth_views
from .views import register, create_ip_account, profile, rate_athlete, public_profile

app_name = 'accounts' 

urlpatterns = [
    path('register/', register, name='register'),
    # Sementara pake Django's built-in login view
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('profile/', profile, name='profile'),
    path('public_profile/<int:athlete_id>/', public_profile, name='public_profile'),
    path('create-ip/', create_ip_account, name='create_ip_account'),
    path('rate/<int:athlete_id>/', rate_athlete, name='rate_athlete'),
]
