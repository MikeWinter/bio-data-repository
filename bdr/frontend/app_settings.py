from django.conf import settings

CACHE_ROOT = getattr(settings, 'BDR_CACHE_ROOT', '.cache')
STORAGE_URL = getattr(settings, 'BDR_STORAGE_URL', 'http://127.0.0.1/')
