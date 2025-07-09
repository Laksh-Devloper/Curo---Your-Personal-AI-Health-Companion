# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import SignUpForm, LoginForm
from .models import CustomUser, Contact, EmailVerification, cipher_suite
from django.http import HttpResponse, HttpRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from google.oauth2 import id_token
from google.auth.transport import requests
from twilio.rest import Client
from django.conf import settings
from twilio.base.exceptions import TwilioRestException
import random
import uuid
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.forms import PasswordResetForm
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site

def index_view(request):
    return render(request, 'index.html')

def google_login(request):
    return render(request, 'google_login.html')

def profile_view(request):
    return render(request, 'profile.html')


@csrf_exempt
def auth_receiver(request):
    if request.method == 'POST':
        token = request.POST.get('credential')
        try:
            user_data = id_token.verify_oauth2_token(
                token, requests.Request(), settings.GOOGLE_OAUTH_CLIENT_ID
            )
            print(f"Google User Data: {user_data}")
            email = user_data['email']
            username = user_data.get('given_name', email.split('@')[0])
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    'username': username[:30],
                }
            )
            if created:
                user.set_unusable_password()
                user.email_verified = True
                user.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            print(f"Logged in user: {user.username}")
            return redirect('profile')
        except ValueError:
            return HttpResponse("Invalid Google token", status=403)
    return HttpResponse("Method not allowed", status=405)

def signup_view(request):
    if request.method == 'POST':
        signup_form = SignUpForm(request.POST)
        if signup_form.is_valid():
            user = signup_form.save(commit=False)
            password = signup_form.cleaned_data['password']
            user.set_password(password)
            user.encrypted_password = cipher_suite.encrypt(password.encode())
            user.email_verified = False
            user.save()
            # CHANGED: Check for existing EmailVerification and delete if exists
            EmailVerification.objects.filter(email=user.email).delete()
            verification = EmailVerification.objects.create(
                email=user.email,
                token=uuid.uuid4(),
                expires_at=timezone.now() + timezone.timedelta(hours=24)
            )
            verification_link = request.build_absolute_uri(
                reverse('verify_email', kwargs={'token': str(verification.token)})
            )
            subject = 'Verify Your Email - Case Companion'
            message = f'Hi,\n\nPlease click the link below to verify your email:\n{verification_link}\n\nThis link is valid for 24 hours.\n\nThank you,\nCase Companion Team'
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.success(request, 'Account created! Please check your inbox to verify your email.')
            except Exception as e:
                messages.error(request, f'Failed to send verification email: {str(e)}')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        signup_form = SignUpForm()
    return render(request, 'login.html', {'signup_form': signup_form, 'form_type': 'signup'})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                if user.email_verified:
                    login(request, user)
                    return redirect('chat_room')
                else:
                    messages.error(request, 'Please verify your email before logging in.')
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'login_form': form, 'form_type': 'login'})

def logout_view(request):
    logout(request)
    return redirect('index')



@method_decorator(csrf_exempt, name='dispatch')
class AuthGoogle(APIView):
    def post(self, request, *args, **kwargs):
        try:
            user_data = self.get_google_user_data(request)
        except ValueError:
            return HttpResponse("Invalid Google token", status=403)
        email = user_data["email"]
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                "username": user_data.get("given_name", email.split('@')[0]),
                "first_name": user_data.get("given_name", ""),
            }
        )
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('profile')

    @staticmethod
    def get_google_user_data(request: HttpRequest):
        token = request.POST['credential']
        return id_token.verify_oauth2_token(
            token, Requests.Request(), settings.GOOGLE_OAUTH_CLIENT_ID
        )

def profile_view(request):
    if request.user.is_authenticated:
        return render(request, 'profile.html', {'user': request.user})
    return redirect('login')

