# accounts/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('google_login/', views.google_login, name='google_login'),
    path('auth-google/', views.AuthGoogle.as_view(), name='auth_google'),
    path('profile/', views.profile_view, name='profile'),
    path('auth-receiver/', views.auth_receiver, name='auth_receiver'),
]