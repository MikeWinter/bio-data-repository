import os.path
import stat

from django.conf import settings


STORAGE_ROOT = getattr(settings, 'BDR_STORAGE_ROOT', os.path.join(os.path.dirname(__file__), 'data'))
STORAGE_MODE = getattr(settings, 'BDR_STORAGE_MODE', stat.S_IWUSR | stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP
                       | stat.S_IWGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
