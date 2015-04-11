import os

from django.core.management.base import NoArgsCommand, CommandError


class Command(NoArgsCommand):
    can_import_settings = True
    help = "Clears the API cache."

    def handle_noargs(self, **options):
        from bdr.frontend import app_settings
        base_path = app_settings.CACHE_ROOT
        deleted = 0

        self.stdout.write("Removing cache files from %s/..." % base_path)
        for path in os.listdir(base_path):
            rel_path = os.path.join(base_path, path)
            try:
                os.unlink(rel_path)
                deleted += 1
            except OSError as err:
                raise CommandError("Could not delete %s: %s. Check that the server is not running and try again."
                                   % (rel_path, err.strerror))
        self.stdout.write("Deleted %i file(s)." % deleted)
