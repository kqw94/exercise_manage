from .base import *


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'exercise_db_0421',
        'USER': 'root',
        'PASSWORD': 'swt@Ddd963741000',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES', character_set_connection='utf8mb4', collation_connection='utf8mb4_unicode_ci'",
            'unix_socket':'/tmp/mysql.sock'
        }
    }
}
