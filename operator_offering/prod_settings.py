from pathlib import Path

from variables import CSRF_TRUSTED, ALLOWED_HOSTS_SETTINGS, DATABASES_SETTINGS, SECRET_KEY_SETTINGS

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SECRET_KEY_SETTINGS

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

CSRF_TRUSTED_ORIGINS = CSRF_TRUSTED

ALLOWED_HOSTS = ALLOWED_HOSTS_SETTINGS

DATABASES = DATABASES_SETTINGS

STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'