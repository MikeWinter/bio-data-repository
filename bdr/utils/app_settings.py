from django.conf import settings

ARCHIVE_READERS = getattr(settings, 'BDR_ARCHIVE_READERS', [])
ARCHIVE_READERS.extend(['bdr.utils.archives.TarArchive', 'bdr.utils.archives.ZipArchive',
                        'bdr.utils.archives.GzipArchive', 'bdr.utils.archives.MockArchive'])

REMOTE_TRANSPORTS = getattr(settings, 'BDR_REMOTE_TRANSPORTS', {})
REMOTE_TRANSPORTS.update({'ftp': 'bdr.utils.transports.FtpTransport', 'http': 'bdr.utils.transports.HttpTransport'})
