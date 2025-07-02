from django.urls import path, reverse_lazy
from allauth.account.views import LoginView, LogoutView
from .views import (
    create_ip_account,
    profile,
    rate_athlete,
    public_profile,
    create_manual_rating,
    admin_finalize_ratings,
    finalize_rating_admin,
    ref_check, 
    ref_confirm,
    CustomSignupView,
    CustomAccountUpdateView,
    account_security_settings,
    verify_current_email_otp,
    change_new_email,
    request_email_change,
)
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from .forms import CustomPasswordChangeForm

urlpatterns = [
    # Custom Signup (daftar) 3-page confirmation (cek referensi -> bikin akun sesuai data)
    path("signup/ref-check/", ref_check, name="account_ref_check"),
    path("signup/ref-confirm/", ref_confirm, name="account_ref_confirm"),
    path(
        'signup/',
        CustomSignupView.as_view(),
        name='account_signup'
    ),
    # Allauth login/logout pake template custom
    path(
        'login/',
        LoginView.as_view(template_name='accounts/login.html'),
        name='account_login'
    ),
    path(
        'logout/',
        LogoutView.as_view(),
        name='account_logout'
    ),

    # Profile and account management
    path('profile/', profile, name='profile'),
    path("settings/", CustomAccountUpdateView.as_view(), name="edit_profile"),
    path('account_security/', account_security_settings, name='account_security_settings'),
    
    # Account Security Settings
    path('account_security/request_email_change/', request_email_change, name='request_email_change'),
    path('account_security/verify_otp/', verify_current_email_otp, name='verify_current_email_otp'),
    path('account_security/change_new_email/', change_new_email, name='change_new_email'),
    path(
      'password_change/',
      PasswordChangeView.as_view(
        form_class=CustomPasswordChangeForm,
        template_name='accounts/password_change.html',
        success_url=reverse_lazy('password_change_done')
      ),
      name='password_change'
    ),
    path(
      'password_change/done/',
      PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
      ),
      name='password_change_done'
    ),

    # Halaman public profile
    path('public_profile/<int:athlete_id>/', public_profile, name='public_profile'),

    # IP and rating flows
    path('create-ip/', create_ip_account, name='create_ip_account'),
    path('rate/<int:athlete_id>/', rate_athlete, name='rate_athlete'),
    path('manual_rating/', create_manual_rating, name='create_manual_rating'),
    path('admin_finalize_ratings/', admin_finalize_ratings, name='admin_finalize_ratings'),
    path(
        'finalize_rating_admin/<int:athlete_id>/',
        finalize_rating_admin,
        name='finalize_rating_admin'
    ),
]
