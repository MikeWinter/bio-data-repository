import os.path

from django.conf import settings


STORAGE_ROOT = getattr(settings, 'BDR_STORAGE_ROOT', os.path.join(os.path.dirname(__file__), 'data'))
