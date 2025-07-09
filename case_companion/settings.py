from pathlib import Path
import certifi
import ssl
from django.core.mail.backends.smtp import EmailBackend as DefaultEmailBackend

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = ''
DEBUG = True
ALLOWED_HOSTS = []

# settings.py (add at the bottom)
# settings.py (replace the old TWILIO stuff at the bottom)
TWILIO_ACCOUNT_SID = ''
TWILIO_AUTH_TOKEN = ''
TWILIO_VERIFY_SERVICE_SID = ''

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'chat',
    'sim',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'case_companion.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'case_companion.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Define custom user model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Redirects
LOGIN_REDIRECT_URL = 'profile'
LOGOUT_REDIRECT_URL = 'index'
login_url = 'login'
# Custom Email Backend with Proper SSL
class CustomEmailBackend(DefaultEmailBackend):
    def __init__(self, host=None, port=None, username=None, password=None, use_tls=None, fail_silently=False, timeout=None, **kwargs):
        super().__init__(
            host=host or 'smtp.gmail.com',
            port=port or 587,
            username=username,
            password=password,
            use_tls=use_tls if use_tls is not None else True,
            fail_silently=fail_silently,
            timeout=timeout or 10,
            **kwargs
        )
        # Use certifi’s CA bundle
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())

    def open(self):
        if self.connection:
            return False
        try:
            self.connection = self.connection_class(self.host, self.port, timeout=self.timeout)
            if self.use_tls:
                self.connection.starttls(context=self.ssl_context)
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except Exception as e:
            if not self.fail_silently:
                raise
            return False

# Email settings
EMAIL_BACKEND = 'case_companion.settings.CustomEmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''  # Replace with your Gmail App Password
EMAIL_TIMEOUT = 10  # Add timeout for stability

# Google Sign-In settings
GOOGLE_OAUTH_CLIENT_ID = ""
if not GOOGLE_OAUTH_CLIENT_ID:
    raise ValueError("GOOGLE_OAUTH_CLIENT_ID missing in .env")

SECURE_REFERRER_POLICY = 'no-referrer-when-downgrade'
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"


# curo_health/settings.py
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "case_companion/static"]
