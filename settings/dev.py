# settings/dev.py
from .base import *

DEBUG = True

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'exercise_db',
        'USER': 'root',
        'PASSWORD': 'kqw19941210',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES', character_set_connection='utf8mb4', collation_connection='utf8mb4_unicode_ci'",
        }
    }
}
