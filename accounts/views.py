from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import CustomUserCreationForm

# Create your views here.

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Setelah registrasi, redirect ke home page
            return redirect('dashboard:home')
        else:
            # Ini sementara : buat ngasih liat error pas debugging
            print(form.errors)
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})
