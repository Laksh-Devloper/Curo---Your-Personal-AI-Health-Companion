# case_companion/urls.py
from django.contrib import admin
from django.urls import path, include
from accounts import views  

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index_view, name='index'),  # Root is now home page
    path('accounts/', include('accounts.urls')),
    path('chat/', include('chat.urls')),
    path('sim/', include('sim.urls')),  # Move sim to /sim/
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('google_login/', views.google_login, name='google_login'),
    path('auth-google/', views.AuthGoogle.as_view(), name='auth_google'),
    path('profile/', views.profile_view, name='profile'),
    path('auth-receiver/', views.auth_receiver, name='auth_receiver'),

]