from .settings import *

DEBUG = False

# Update with your DigitalOcean server IP or domain
ALLOWED_HOSTS = ['104.248.97.115', 'localhost', '127.0.0.1']

# Update CSRF settings
CSRF_TRUSTED_ORIGINS = ['http://104.248.97.115']

# Security settings
SECURE_SSL_REDIRECT = False  # Set to True only after setting up SSL
SESSION_COOKIE_SECURE = False  # Set to True only after setting up SSL
CSRF_COOKIE_SECURE = False  # Set to True only after setting up SSL
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# CORS settings - update with your frontend domain
CORS_ALLOW_ALL_ORIGINS = True  # For development, restrict this in production
CORS_ALLOW_CREDENTIALS = True

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
} 