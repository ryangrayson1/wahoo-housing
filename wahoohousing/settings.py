"""
Django settings for housingapp project.

Generated by 'django-admin startproject' using Django 3.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

"""
References:
Title: Deploying Django to Heroku: Connecting Heroku Postgres
URL: https://bennettgarner.medium.com/deploying-django-to-heroku-connecting-heroku-postgres-fcc960d290d1
Title: Provisioning a  Test PostgreSQL database on heroku for your Django App
URL: https://medium.com/analytics-vidhya/provisioning-a-test-postgresql-database-on-heroku-for-your-django-app-febb2b5d3b29

Title: ValueError Missing Staticfiles manifest entry for favicon.ico
https://stackoverflow.com/questions/44160666/valueerror-missing-staticfiles-manifest-entry-for-favicon-ico
"""

from pathlib import Path
import sys, dj_database_url, dotenv, os, dj_database_url, cloudinary, cloudinary.uploader, cloudinary.api

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

dotenv_file = os.path.join(BASE_DIR, ".env")
if os.path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-in&*o2ejo$36dwc*t^it_t-8m=*t%cx0_0hr_@w@@z#3v2^=2k'

# SECURITY WARNING: don't run with debug turned on in production!
if os.environ.get('local_dev'):
    DEBUG = True
    DEBUG_PROPAGATE_EXCEPTIONS = True

else:
    DEBUG = False
    DEBUG_PROPAGATE_EXCEPTIONS = True




ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'wahoo-housing.herokuapp.com', 'wahoohousing.herokuapp.com']

# Heroku import
import django_heroku

# database urls import
import dj_database_url

# Application definition

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'cloudinary_storage',
    'cloudinary',
    'housingapp.apps.HousingappConfig',
    'bootstrap5',
    'django.contrib.sites',
	'anymail',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

#redirect HTTP to HTTPS just for heroku
if os.environ.get('local_dev') or 'test' in sys.argv or 'Run Tests' in sys.argv:
    SECURE_SSL_REDIRECT = False
else:
    SECURE_SSL_REDIRECT = True

ROOT_URLCONF = 'wahoohousing.urls'

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

WSGI_APPLICATION = 'wahoohousing.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
# DATABASES = {}
# DATABASES['default'] = dj_database_url.config(conn_max_age=600)

if os.environ.get('local_dev'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ['local_dbname'],
            'USER': os.environ['local_dbuser'],
            'PASSWORD': os.environ['local_dbpwd'],
            'HOST': 'localhost',  # '127.0.0.1' probably works also
            'PORT': '5432',
        }
    }

elif os.environ.get('GITHUB_WORKFLOW'):
    DATABASES = {
        'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'github_actions',
           'USER': 'postgres',
           'PASSWORD': 'postgres',
           'HOST': '127.0.0.1',
           'PORT': '5432',
        }
    }
else:
    #DATABASES = {}
    #DATABASES['default'].update(dj_database_url.config(conn_max_age=600))
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600)
    }

# import dj_database_url
MEDIA_URL = '/housingapp/images/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'housingapp/images')

#Cloudinary setup
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# DATABASES['default'].update(dj_database_url.config(conn_max_age=600))

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = str(Path().resolve()) + 'static'
STATICFILES_DIRS = (str(BASE_DIR.joinpath('static')),)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
#STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Activate Django-Heroku
django_heroku.settings(locals())

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend'
]

# Redirect urls
LOGIN_REDIRECT_URL = "/"

SITE_ID = 1

# Provider specific settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        # For each OAuth based provider, either add a ``SocialApp``
        # (``socialaccount`` app) containing the required client
        # credentials, or list them here:
        'APP': {
            'client_id': '701216368555-nklj3o5mkd8chcfbs1419a2af3deqim1.apps.googleusercontent.com',
            'secret': 'aGxJjShliZg2PXtzmaRBA6s3',
            'key': ''
        },
        'SCOPE': {
            'profile',
            'email'
        }
    }
}

#Anymail setup
EMAIL_BACKEND = "anymail.backends.sendinblue.EmailBackend"
DEFAULT_FROM_EMAIL = SERVER_EMAIL = 'wahoohousing@gmail.com'

#Cloudinary config
CLOUDINARY_STORAGE = {
    'CLOUD_NAME' : "wahoo-housing",
    'API_SECRET' : "VAQLQcTQeCfDXIEZb8qfpewkB20",
	'API_KEY' : "319157633385814"
}

ANYMAIL = {
    "SENDINBLUE_API_KEY": "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",
	"IGNORE_RECIPIENT_STATUS": True,
	"ANYMAIL_IGNORE_UNSUPPORTED_FEATURES": True
}


# SSL mode fix for postgres
options = DATABASES['default'].get('OPTIONS', {})
options.pop('sslmode', None)
