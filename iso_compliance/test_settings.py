import os
os.environ.setdefault('SECRET_KEY', 'test-secret-key-not-for-production')
os.environ.setdefault('DB_NAME', 'dummy')
os.environ.setdefault('DB_USER', 'dummy')
os.environ.setdefault('DB_PASSWORD', 'dummy')
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('BACK_BLAZE_KEY_ID', 'dummy')
os.environ.setdefault('BACK_BLAZE_BUCKET_NAME', 'dummy')
os.environ.setdefault('BACK_BLAZE_APLLICATION_KEY', 'dummy')

from .settings import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
LIGHTNING_MOCK_MODE = True
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']  # faster tests