# Amir Keivan Mohtashami
# Amirmohsen Ahanchi
# Mohammad Javad Naderi

"""
Django settings for cps project.

Generated by 'django-admin startproject' using Django 1.9.7.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os

import logging

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'd#kb9j&&o5t!p(^cj!2c6#e!g5_)9yj-m%%d!djxmasi5eu1ir'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

SITE_ID = 1

# Application definition

INSTALLED_APPS = [
    # Django Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',


    # Vendor Apps
    'bootstrap3',
    'import_export',

    # CPS Apps
    'core',
    'accounts',
    'problems',
    'judge',
    'file_repository',
    'runner',
    'tasks',
    'trader',

    # Allauth Apps (must be after accounts)
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'cps.middlewares.middleware.LoginRequiredMiddleware'
]

ROOT_URLCONF = 'cps.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'problems.views.context_processors.revision_data',
            ],
        },
    },
]

WSGI_APPLICATION = 'cps.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Accounts and Auth
# https://django-allauth.readthedocs.io/en/latest/configuration.html

AUTH_USER_MODEL = 'accounts.User'

ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',
    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',

    # Problem role permission backend
    'problems.backends.ProblemRoleBackend',
)

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "assets"),
]

STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), "static")

MEDIA_ROOT = os.path.join(BASE_DIR, 'storage')
MEDIA_URL = "/storage/"

# project settings

# fail-safe time limit in seconds (float)
FAILSAFE_TIME_LIMIT = 30

# fail-safe memory limit in MB (int)
FAILSAFE_MEMORY_LIMIT = 512

SANDBOX_TEMP_DIR = "/tmp"
# SANDBOX_TEMP_DIR = os.path.join(BASE_DIR, "tmp")

# sandbox
SANDBOX_KEEP = True
SANDBOX_USE_CGROUPS = True
SANDBOX_MAX_FILE_SIZE = 1048576

# isolate
ISOLATE_PATH = os.path.join(BASE_DIR, "../isolate/isolate")

BOOTSTRAP3 = {
    'field_renderers': {
        'default': 'bootstrap3.renderers.FieldRenderer',
        'inline': 'bootstrap3.renderers.InlineFieldRenderer',
        'readonly': 'problems.forms.renderers.ReadOnlyFieldRenderer',
    },
}

LOGIN_REQUIRED_URLS_EXCEPTIONS = (
    r'/accounts/login/$',
    r'/accounts/logout/$',
    r'/admin/login/$',
    r'/admin/$'
)

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'

JUDGE_DEFAULT_NAME = 'local_runner'

JUDGE_HANDLERS = {
    'local_runner': {
        'class': 'judges.runner.Runner',
        'parameters': {
            'compile_time_limit': 30,
            'compile_memory_limit': 1024,
        }
    }
}

CELERY_MAX_RETRIES = None

DISABLE_BRANCHES = False


try:
    from .local_settings import *
except:
    pass