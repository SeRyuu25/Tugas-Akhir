from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import register, create_ip_account, profile, rate_athlete, public_profile, create_manual_rating, admin_finalize_ratings, finalize_rating_admin, update_profile
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView

app_name = 'accounts' 

urlpatterns = [
    path('register/', register, name='register'),
    # Sementara pake Django's built-in login view
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('profile/', profile, name='profile'),
    path('update/', update_profile, name='update_profile'),
    path('password_change/', PasswordChangeView.as_view(
          template_name='accounts/password_change.html',
          success_url=reverse_lazy('accounts:password_change_done')
         ), name='password_change'),
    path('password_change/done/', PasswordChangeDoneView.as_view(
          template_name='accounts/password_change_done.html'
         ), name='password_change_done'),
    path('public_profile/<int:athlete_id>/', public_profile, name='public_profile'),
    path('create-ip/', create_ip_account, name='create_ip_account'),
    path('rate/<int:athlete_id>/', rate_athlete, name='rate_athlete'),
    path('manual_rating/', create_manual_rating, name='create_manual_rating'),
    path('admin_finalize_ratings/', admin_finalize_ratings, name='admin_finalize_ratings'),
    path('finalize_rating_admin/<int:athlete_id>/', finalize_rating_admin, name='finalize_rating_admin'),
]
