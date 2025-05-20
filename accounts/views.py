from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Avg
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from .forms import IPAccountCreationForm, IPRatingOpinionForm, ManualIPOpinionForm, CustomAccountUpdateForm, ReferenceCheckForm
from tournaments.models import Tournament, Match
from accounts.models import CustomUser, AthleteProfile, IPRatingOpinion, AthleteAccountReference

from allauth.account.views import SignupView
from allauth.account.models import EmailAddress, EmailConfirmation
from allauth.account.utils import send_email_confirmation

from datetime import timedelta
import random
import string

# Create your views here.

# Cek akun admin ato bukan
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'admin')

# Cek akun IP ato bukan 
def is_ip(user):
    return user.is_authenticated and (user.role == 'ip' or user.is_superuser or user.role == 'admin')

# Buat cek referensi atlet pas ada atlet yang daftar (pendaftaran atlet)
def ref_check(request):
    if request.method == "POST":
        form = ReferenceCheckForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # store in session  
            request.session["ref_nickname"] = data["nickname"]
            request.session["ref_ptm"]      = data["ptm"]
            request.session["is_new_player"] = data["is_new"]
            if not data["is_new"]:
                request.session["ref_id"] = data["reference"].pk
                return redirect("account_ref_confirm")
            return redirect("account_signup")  # skip confirm for new
    else:
        form = ReferenceCheckForm()
    return render(request, "accounts/ref_check.html", {"form": form})

# Buat konfirmasi kalo atlet ada di reference (atlet yang daftar konfirmasi data)
def ref_confirm(request):
    ref = AthleteAccountReference.objects.get(pk=request.session["ref_id"])
    if request.method == "POST":
        if "back" in request.POST:
            return redirect("account_ref_check")
        return redirect("account_signup")
    return render(request, "accounts/ref_confirm.html", {"reference": ref})

import logging
logger = logging.getLogger(__name__)

# Buat Sign up (daftar) setelah page ref_check & ref_confirm
class CustomSignupView(SignupView):
    template_name = "accounts/signup.html"

    def get_initial(self):
        init = super().get_initial()
        init.update({
            "nickname": self.request.session.get("ref_nickname",""),
            "email":    "",  # leave blank
        })
        return init

    def form_valid(self, form):
        # first let allauth create the user
        resp = super().form_valid(form)
        user = self.user
        if user.role == "atlet":
          profile, created = AthleteProfile.objects.get_or_create(user=user)
          if not created:
              logger.debug("Profile already exists for user: %s", user.username)
        # set ptm & previous_divisi
        user.ptm = self.request.session.get("ref_ptm", "")
        if self.request.session.get("is_new_player", True):
            profile.previous_divisi = "pemain baru"
        else:
            ref = AthleteAccountReference.objects.get(pk=self.request.session["ref_id"])
            profile.previous_divisi = ref.divisi
            ref.sudah_ada_akun = True
            ref.save()
        user.save()
        profile.save()
        # clear session
        for k in ("ref_nickname","ref_ptm","ref_id","is_new_player"):
            self.request.session.pop(k, None)
        return resp

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

# Buat Profile
@login_required
def profile(request):
    user = request.user
    if user.role == 'atlet':
        # For athlete accounts: show profile data, upcoming & finished tournaments, and match records.
        athlete_profile = user.athlete_profile
        upcoming_tournaments = Tournament.objects.filter(
            participants=athlete_profile,  # use the participants relation
            start_date__gte=timezone.now()  # gte = greater than / equal
        )
        finished_tournaments = Tournament.objects.filter(
            participants=athlete_profile,
            start_date__lt=timezone.now()  # lt = less than
        )
        matches = Match.objects.filter(
            Q(athlete1=athlete_profile) | Q(athlete2=athlete_profile)
        ).order_by('-match_date')
        context = {
            'athlete_profile': athlete_profile,
            'upcoming_tournaments': upcoming_tournaments,
            'finished_tournaments': finished_tournaments,
            'matches': matches,
        }
        return render(request, 'accounts/athlete_profile.html', context)
    elif user.role == 'ip':
        # For IP accounts: show tournaments hosted by the IP, pending registered athletes, and manual opinions.
        tournaments_hosted = Tournament.objects.filter(host=user)
        pending_athletes = AthleteProfile.objects.filter(initial_rating_finalized=False).exclude(ip_opinions__ip_account=request.user)
        manual_opinions = IPRatingOpinion.objects.filter(ip_account=user, athlete__isnull=True)
        context = {
            'tournaments_hosted': tournaments_hosted,
            'pending_athletes': pending_athletes,
            'manual_opinions': manual_opinions,
        }
        return render(request, 'accounts/ip_profile.html', context)
    else:
        # For other roles (e.g. admin) you can render a default profile page.
        return render(request, 'accounts/profile.html')

# Buat Profile yang bisa diliat publik
def public_profile(request, athlete_id):
    athlete = get_object_or_404(AthleteProfile, id=athlete_id)
    return render(request, 'accounts/public_profile.html', {'athlete': athlete})

# Buat update profile akun
class CustomAccountUpdateView(LoginRequiredMixin, UpdateView):
    model         = CustomUser
    form_class    = CustomAccountUpdateForm
    template_name = "accounts/update_profile.html"
    success_url   = reverse_lazy("profile")
    
    def get_object(self):
        # always edit the logged-in user
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['email'] = self.request.user.email
        context['ptm'] = self.request.user.ptm
        return context

# Fungsi buat generate random OTP
def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

# Fungsi Rate-limiting: buat mastiin / security ke spam minta OTP (harus nunggu dulu jadinya)
def is_rate_limited(user_id):
    last_request_time = cache.get(f"otp_request_time_{user_id}")
    if last_request_time:
        time_diff = timezone.now() - last_request_time
        if time_diff.seconds < 60:  # Limit requests to 1 per minute
            return True
    cache.set(f"otp_request_time_{user_id}", timezone.now(), timeout=3600)  # Store timestamp for 1 hour
    return False

# Buat halaman keamanan akun (ganti email & password)
@login_required
def account_security_settings(request):
    if request.method == 'POST':
        # Change Email Process
        if 'change_email' in request.POST:
            # Step 1: Send OTP to current email address
            if is_rate_limited(request.user.id):
                messages.error(request, "Too many OTP requests. Please try again later.Terlalu banyak permintaan OTP. Mohon tunggu sebentar lalu coba kembali.")
                return redirect('account_security_settings')
            
            otp = generate_otp()
            send_mail(
                'Your OTP for email change',
                f'Your OTP is {otp}',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],  # Send OTP to the current email
            )
            cache.set(f"otp_{request.user.id}", otp, timeout=300)  # OTP valid for 5 minutes

            return redirect('verify_current_email_otp')  # Redirect to OTP verification page

        # Password Change Process (handled by Allauth)
        elif 'change_password' in request.POST:
            return redirect('password_change')  # Let Allauth handle the password change

    return render(request, 'accounts/account_security_settings.html')

# Buat ngirim OTP ke email skrng (cek user)
@login_required
def request_email_change(request):
    if request.method == 'POST':
        # Step 1: Send OTP to current email address
        otp = generate_otp()
        send_mail(
            'Your OTP for email change',
            f'Your OTP is {otp}',
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],  # Send OTP to the current email
        )

        # Store OTP temporarily for verification
        cache.set(f"otp_{request.user.id}", otp, timeout=300)  # OTP valid for 5 minutes

        return redirect('verify_current_email_otp')  # Redirect to OTP verification page

    return render(request, 'accounts/request_email_change.html')

# Buat cek OTP yang dimasukin bener ato engga (pas cek user, lanjutan dari request_email_change)
@login_required
def verify_current_email_otp(request):
    if request.method == 'POST':
        otp_entered = request.POST['otp']
        stored_otp = cache.get(f"otp_{request.user.id}")

        if otp_entered == stored_otp:
            # OTP is valid, proceed to change the email
            return redirect('change_new_email')  # Redirect to the new email input form
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'accounts/verify_current_email_otp.html')

EXPIRY_HOURS = 24

# Buat ganti email (pas cek user udh selesai)
@login_required
def change_new_email(request):
    user = request.user

    # Buat delete pending email yg expired
    if user.pending_email and user.pending_email_requested_at:
        age = timezone.now() - user.pending_email_requested_at
        if age > timedelta(hours=EXPIRY_HOURS):
            EmailAddress.objects.filter(
                user=user,
                email=user.pending_email,
                verified=False,
                primary=False
            ).delete()
            user.pending_email = None
            user.pending_email_requested_at = None
            user.save()

    if request.method == "POST":
        new_email = request.POST.get("new_email").strip().lower()

        if EmailAddress.objects.filter(email__iexact=new_email) \
                                .exclude(user=user).exists():
            messages.error(request, "That email address is already in use by another account.")
            return redirect("account_security_settings")

        # 1) Create (or reset) a non-primary, unverified EmailAddress
        email_address, created = EmailAddress.objects.get_or_create(
            user=user,
            email=new_email,
            defaults={"verified": False, "primary": False},
        )
        if not created:
            email_address.verified = False
            email_address.primary = False
            email_address.save()

        # 2) If it's already the active address, bail out
        if email_address.primary and email_address.verified:
            messages.error(request, "This email is already associated with your account.")
            return redirect('account_security_settings')

        # 3) Store the pending email so your signal knows what to swap later
        user.pending_email = new_email
        user.pending_email_requested_at = timezone.now()
        user.save()

        # 4) Send the confirmation link to the new address
        send_email_confirmation(request, user, email=new_email)
        return redirect('account_security_settings')

    # GET: just show the form
    return render(request, 'accounts/change_new_email.html')

# Buat ngasih initial rating ke atlet (dari IP)    
@login_required
@user_passes_test(is_ip)
def rate_athlete(request, athlete_id):
    # For a registered athlete (AthleteProfile), allow the IP to submit an opinion.
    athlete = get_object_or_404(AthleteProfile, id=athlete_id)
    if IPRatingOpinion.objects.filter(ip_account=request.user, athlete=athlete).exists():
        messages.error(request, "Anda sudah memberikan rating untuk atlet ini.")
        return redirect('profile')
    if request.method == 'POST':
        form = IPRatingOpinionForm(request.POST)
        if not request.POST.get("confirm_rating"):
            # Add a non-field error so it shows up at top of form
            form.add_error(None, "Harap centang kotak konfirmasi rating sebelum menyimpan.")
        elif form.is_valid():
            opinion = form.save(commit=False)
            opinion.ip_account        = request.user
            opinion.athlete           = athlete
            opinion.athlete_identifier = athlete.user.nickname
            opinion.save()
            messages.success(request, "Rating berhasil disimpan!")
            return redirect("profile")
    else:
        form = IPRatingOpinionForm(initial={'athlete_identifier': athlete.user.username})
    return render(request, 'accounts/rate_athlete.html', {'form': form, 'athlete': athlete})

# Kalau butuh manual rating, bisa pake fungsi ini
@login_required
@user_passes_test(is_ip)
def create_manual_rating(request):
    if request.method == 'POST':
        form = ManualIPOpinionForm(request.POST)
        if form.is_valid():
            opinion = form.save(commit=False)
            opinion.ip_account = request.user
            opinion.save()
            messages.success(request, "Rating Anda telah disimpan.")
            return redirect('accounts:profile')
    else:
        form = ManualIPOpinionForm()
    return render(request, 'accounts/create_manual_rating.html', {'form': form})

# nanti ini cek bedanya apa sama finalize_rating_admin
def finalize_initial_rating(athlete):
    """
    Averages all IP opinions linked to this athlete, updates athlete's current_rating,
    and sets initial_rating_finalized=True.
    Returns a message describing the result.
    """
    # Get all opinions referencing this athlete
    opinions = athlete.ip_opinions.all()
    if not opinions.exists():
        return "Belum ada yang memberikan rating untuk atlet ini."
    
    # Calculate average rating from the 'opinion_rating' field
    avg_rating = opinions.aggregate(Avg('opinion_rating'))['opinion_rating__avg']
    if avg_rating is None:
        return "Tidak bisa menentukan rating rata-rata."
    
    # Update athlete's current_rating and mark as finalized
    athlete.current_rating = round(avg_rating)
    athlete.initial_rating_finalized = True
    athlete.save()
    
    return f"Finalisasi rating awal pada nilai {athlete.current_rating}."

# Buat admin profile -> ngasih list yg blom finalized
@login_required
@user_passes_test(is_admin)
def admin_finalize_ratings(request):
    # Get all AthleteProfile objects that have not been finalized
    athletes = AthleteProfile.objects.filter(initial_rating_finalized=False)
    context = {
        'athletes': athletes,
    }
    return render(request, 'accounts/admin_finalize_ratings.html', context)

# Buat finalisasi rating atlet (pas tombol ditekan)
@login_required
@user_passes_test(is_admin)
def finalize_rating_admin(request, athlete_id):
    athlete = get_object_or_404(AthleteProfile, id=athlete_id, initial_rating_finalized=False)
    # Get the average of all IP opinions linked to this athlete
    opinions = athlete.ip_opinions.all()
    if opinions.exists():
        avg_rating = opinions.aggregate(Avg('opinion_rating'))['opinion_rating__avg']
        athlete.current_rating = round(avg_rating)
        athlete.initial_rating_finalized = True
        athlete.save()
        messages.success(request, f"Rating awal {athlete.user.nickname} berhasil difinalisasi dengan rating {athlete.current_rating}.")
    else:
        messages.error(request, "Belum ada yang memberikan rating untuk atlet ini.")
    return redirect('accounts:admin_finalize_ratings')