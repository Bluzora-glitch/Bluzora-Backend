import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# สำหรับการตั้งค่า DEBUG จาก .env
DEBUG = os.getenv('DEBUG') == 'True'

# โหลดค่า .env
load_dotenv()

# กำหนด BASE_DIR เพียงครั้งเดียว
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_URL = '/static/'

if not DEBUG:
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # ใช้ใน production
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# Allowed hosts (เพิ่มโดเมนที่จำเป็น)
ALLOWED_HOSTS = ['bluzora-backend.onrender.com', 'www.bluzora-backend.onrender.com', 'localhost', '127.0.0.1']
# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'rest_framework',
    'django_filters',
    'crops',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

# CORS configuration
CORS_ALLOW_ALL_ORIGINS = True  # หรือระบุรายการ origins ที่อนุญาต

# REST framework settings
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_CHARSET': 'utf-8',
}

ROOT_URLCONF = 'price_prediction.urls'

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

WSGI_APPLICATION = 'price_prediction.wsgi.application'

# Database settings using DATABASE_URL from .env
DATABASE_URL = os.getenv('DATABASE_URL')

DATABASES = {
    'default': dj_database_url.config(default=DATABASE_URL) if DATABASE_URL else {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME').strip(),  # ใช้ .strip() เพื่อลบช่องว่างจากชื่อฐานข้อมูล
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),  # ใช้ localhost ในเครื่อง local
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

MEDIA_URL = '/media/'  # URL สำหรับการเข้าถึงไฟล์
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # ที่เก็บไฟล์ที่อัปโหลดในเซิร์ฟเวอร์

# Internationalization settings
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
