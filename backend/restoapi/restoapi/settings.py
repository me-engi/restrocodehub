# backend/culinary_api/settings.py
import os
from pathlib import Path
from decouple import config, Csv # For python-decouple

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Core Django Settings ---
SECRET_KEY = config('SECRET_KEY') # Loaded from .env
DEBUG = config('DEBUG', default=False, cast=bool) # Loaded from .env, defaults to False

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv(), default='127.0.0.1,localhost')

# --- Application Definition ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth', # Still needed even with custom user model for permissions framework
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party Apps
    'rest_framework',
    'rest_framework.authtoken', # If using DRF's built-in token auth (can be removed if only JWT)
    'corsheaders',              # For Cross-Origin Resource Sharing
    # 'django_filters',         # For advanced filtering in DRF (install if used)
    # 'storages',             # If using S3 for static/media files (install if used)

    # Your Apps (ensure correct AppConfig names if you customized them)
    'users.apps.UsersConfig',
    'restaurants.apps.RestaurantsConfig',
    'menu.apps.MenuConfig',
    'orders.apps.OrdersConfig',
    'payments.apps.PaymentsConfig',
    'pos_integration.apps.PosIntegrationConfig',
    'ai_engine.apps.AiEngineConfig',
    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware', # CORS middleware, usually high up
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', # Important for session auth / forms
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Handles user session
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'restoapi.urls' # Assuming your project folder is 'culinary_api'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Optional: Project-level templates directory
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

WSGI_APPLICATION = 'culinary_api.wsgi.application'


# --- Database Configuration ---
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': config('DATABASE_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': config('DATABASE_NAME', default=BASE_DIR / 'db.sqlite3'),
        'USER': config('DATABASE_USER', default=''),
        'PASSWORD': config('DATABASE_PASSWORD', default=''),
        'HOST': config('DATABASE_HOST', default=''),
        'PORT': config('DATABASE_PORT', default=''),
    }
}
# Example for PostgreSQL using dj-database-url (install it: pip install dj-database-url)
# import dj_database_url
# DATABASES['default'] = dj_database_url.config(default=config('DATABASE_URL'), conn_max_age=600)
# In .env: DATABASE_URL=postgres://user:password@host:port/dbname


# --- Password Validation ---
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Internationalization ---
# https://docs.djangoproject.com/en/5.0/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC' # Recommended to store datetimes in UTC in the database
USE_I18N = True
USE_TZ = True # Enable timezone-aware datetimes

# --- Static files (CSS, JavaScript, Images for Admin and App Static Assets) ---
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles' # For `collectstatic` in production
STATICFILES_DIRS = [
    BASE_DIR / "static", # Project-level static files
]
# For production, consider using WhiteNoise or S3 for serving static files.
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage' # If using WhiteNoise

# --- Media files (User-uploaded content like images) ---
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# --- Default primary key field type ---
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Custom User Model ---
AUTH_USER_MODEL = 'users.User' # Points to your custom User model in the 'users' app

# --- Django REST Framework Settings ---
# https://www.django-rest-framework.org/api-guide/settings/
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # Use your custom JWT auth or SimpleJWT
        'users.authentication.CustomJWTAuthentication', # Assuming this is where you put it
        # 'rest_framework_simplejwt.authentication.JWTAuthentication', # If using DRF Simple JWT
        'rest_framework.authentication.SessionAuthentication', # For browsable API & Django Admin
        # 'rest_framework.authentication.TokenAuthentication', # If using DRF's built-in Token (less secure than JWT for APIs)
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated', # Default to require authentication
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20, # Default page size for paginated results
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer', # For easy API testing in browser during dev
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',       # For HTML form data
        'rest_framework.parsers.MultiPartParser' # For file uploads
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend', # Install django-filter
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    # Exception handling for consistent API error responses
    # 'EXCEPTION_HANDLER': 'your_project.api_utils.custom_exception_handler', # If you create one
}

# --- CORS (Cross-Origin Resource Sharing) Settings ---
# https://github.com/adamchainz/django-cors-headers
# CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', cast=Csv(), default=[
#     'http://localhost:3000', # Flutter web dev default
#     'http://127.0.0.1:3000',
#     # Add your Flutter app's production domain here
# ])
CORS_ALLOW_ALL_ORIGINS = True
# CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=DEBUG, cast=bool) # More permissive for dev
CORS_ALLOW_CREDENTIALS = True # If your frontend needs to send cookies (e.g., for CSRF with session auth)
# Consider adding more specific CORS settings for production:
# CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']
# CORS_ALLOW_HEADERS = ['authorization', 'content-type', ...]


# --- Email Backend Configuration ---
# https://docs.djangoproject.com/en/5.0/topics/email/
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend') # Console for dev
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=25, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='webmaster@localhost')
# SERVER_EMAIL = config('SERVER_EMAIL', default=DEFAULT_FROM_EMAIL) # For error emails to admins

# --- Logging Configuration (Basic Example) ---
# https://docs.djangoproject.com/en/5.0/topics/logging/
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': { # Example file handler (configure path and rotation for production)
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/django.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'] if DEBUG else ['file'], # Adjust for production
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'] if DEBUG else ['file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': { # Specifically for request errors
            'handlers': ['file'], # Send these to file for sure
            'level': 'ERROR',
            'propagate': False,
        },
        # Your app's loggers
        'users': {'handlers': ['console', 'file'], 'level': 'DEBUG' if DEBUG else 'INFO', 'propagate': False},
        'orders': {'handlers': ['console', 'file'], 'level': 'DEBUG' if DEBUG else 'INFO', 'propagate': False},
        # ... add other app loggers ...
    },
}


# --- Celery Configuration (Optional - Placeholder) ---
# If you use Celery for background tasks
# CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
# CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TIMEZONE = TIME_ZONE


# --- JWT Settings (Specific to your implementation or a library like SimpleJWT) ---
# Example for the custom JWT logic sketched earlier
JWT_SECRET_KEY = config('JWT_SECRET_KEY', default='fallback-secret-key-for-jwt-dev-only')
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = config('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', default=30, cast=int)
JWT_REFRESH_TOKEN_EXPIRE_DAYS = config('JWT_REFRESH_TOKEN_EXPIRE_DAYS', default=7, cast=int)

# If using djangorestframework-simplejwt:
# from datetime import timedelta
# SIMPLE_JWT = {
#     "ACCESS_TOKEN_LIFETIME": timedelta(minutes=config('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', default=30, cast=int)),
#     "REFRESH_TOKEN_LIFETIME": timedelta(days=config('JWT_REFRESH_TOKEN_EXPIRE_DAYS', default=7, cast=int)),
#     "ROTATE_REFRESH_TOKENS": True,
#     "BLACKLIST_AFTER_ROTATION": True,
#     "UPDATE_LAST_LOGIN": True,
#
#     "ALGORITHM": "HS256",
#     "SIGNING_KEY": config('JWT_SECRET_KEY', default=SECRET_KEY), # Can reuse Django SECRET_KEY or have a separate one
#     "VERIFYING_KEY": None,
#     "AUDIENCE": None,
#     "ISSUER": None,
#     "JWK_URL": None,
#     "LEEWAY": 0,
#
#     "AUTH_HEADER_TYPES": ("Bearer",),
#     "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
#     "USER_ID_FIELD": "id", # From your custom User model
#     "USER_ID_CLAIM": "user_id",
#     "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
#
#     "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
#     "TOKEN_TYPE_CLAIM": "token_type",
#     "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
#
#     "JTI_CLAIM": "jti",
#
#     "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
#     "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5), # How often access token can be refreshed
#     "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1), # How long sliding token itself is valid
#
#     # Custom claims (example to include role and tenant_id)
#     # You'd need to create a custom token serializer for this to work
#     # "TOKEN_OBTAIN_SERIALIZER": "users.serializers.MyTokenObtainPairSerializer",
# }


# --- Frontend URL ---
# Used for constructing absolute URLs in emails (e.g., password reset, account activation)
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000') # Your Flutter Web App URL

# --- Security Settings for Production (Uncomment and configure as needed) ---
# if not DEBUG:
#     SECURE_BROWSER_XSS_FILTER = True
#     X_FRAME_OPTIONS = 'DENY'
#     SECURE_SSL_REDIRECT = True # Ensure your site is served over HTTPS
#     SECURE_HSTS_SECONDS = 31536000 # 1 year
#     SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#     SECURE_HSTS_PRELOAD = True
#     SESSION_COOKIE_SECURE = True
#     CSRF_COOKIE_SECURE = True
#     SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') # If behind a proxy like Nginx
#     # For more: https://docs.djangoproject.com/en/5.0/topics/security/