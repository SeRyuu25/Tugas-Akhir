from django.urls import path
from django.contrib.auth import views as auth_views
from .views import register, create_ip_account

app_name = 'accounts' 

urlpatterns = [
    path('register/', register, name='register'),
    # Sementara pake Django's built-in login view
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('create-ip/', create_ip_account, name='create_ip_account'),
]
