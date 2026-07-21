from decouple import config
import os

DJANGO_SETTINGS_MODULE=os.environ.get('DJANGO_SETTINGS_MODULE', config('DJANGO_SETTINGS_MODULE', default='crmcami.settings'))
DB_HOST = os.environ.get('DB_HOST', config('DB_HOST', default='127.0.0.1'))
DEBUG = os.environ.get('DEBUG', config('DEBUG', default=True, cast=bool))
WPUSER = os.environ.get('WPUSER', config('WPUSER'))
WPPASS = os.environ.get('WPPASS', config('WPPASS'))
DB_NAME = os.environ.get('DB_NAME', config('DB_NAME'))
DB_USR = os.environ.get('DB_USR', config('DB_USR'))
DB_PASS = os.environ.get('DB_PASS', config('DB_PASS'))
DB_PORT = os.environ.get('DB_PORT', config('DB_PORT'))
SECRET_KEY = os.environ.get('SECRET_KEY', config('SECRET_KEY'))
APPHOST = os.environ.get('APPHOST', config('APPHOST'))