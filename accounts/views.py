from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import AthleteAccountCreationForm, IPAccountCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test

# Create your views here.

# Buat registrasi akun atlet
def register(request):
    if request.method == 'POST':
        form = AthleteAccountCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Setelah registrasi, redirect ke home page
            return redirect('dashboard:home')
        else:
            # Ini sementara : buat ngasih liat error pas debugging
            print(form.errors)
    else:
        form = AthleteAccountCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

# Cek akun admin ato bukan
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'admin')

# Buat bikin akun IP oleh admin / superuser
@login_required
@user_passes_test(is_admin)
def create_ip_account(request):
    if request.method == 'POST':
        form = IPAccountCreationForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect ke admin page
            return redirect('admin:index')
    else:
        form = IPAccountCreationForm()
    return render(request, 'accounts/create_ip_account.html', {'form': form})