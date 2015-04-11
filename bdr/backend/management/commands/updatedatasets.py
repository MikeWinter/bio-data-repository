"""
Specifies a command for updating datasets in the repository that are out-of-date with respect to their remote data
source.
"""

__author__ = "Michael Winter (mail@michael-winter.me.uk)"
__license__ = """
    Copyright (C) 2015 Michael Winter

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
    """

from datetime import datetime, timedelta
from hashlib import sha1
import errno
import os
import stat
import tempfile

from django.core.management.base import NoArgsCommand
from django.db import transaction
import xdelta

from ... import app_settings, models
from .... import utils
from ....utils.archives import Archive, ZipArchive
from ....utils.transports import Transport, TransportError


class Command(NoArgsCommand):
    """
    Updates datasets in the repository that are out-of-date with respect to their remote data source.
    """
    help = ("Queries the source associated with each dataset in the repository, updating any out-of-date files"
            " encountered.")
    """A short description of the command to be printed in help messages."""

    def handle_noargs(self, **options):
        """
        Iterate over datasets in the repository with remote data sources, and add new revisions for files that have been
        updated.
        """
        for dataset in models.Dataset.objects.all():
            now = datetime.now(utils.utc)
            self.stdout.write('Checking %s (%s)...' % (dataset, now.strftime('%a, %d-%b-%Y %H:%M')))

            # Check if this dataset is due to be updated
            if (dataset.update_frequency == 0 or not dataset.update_uri
                or (dataset.checked_at
                    and dataset.checked_at + timedelta(0, 0, 0, 0, dataset.update_frequency) > now)):
                self.stdout.write('Too soon. Skipping.')
                continue

            dataset.checked_at = now

            try:
                transport = Transport.instance(dataset.update_uri, dataset.update_username, dataset.update_password)
                modification_date = transport.get_modification_date().replace(tzinfo=utils.utc) or now
                size = transport.get_size()
            except TransportError as error:
                self.stderr.write('Retrieving properties failed: %s' % error.message)
                continue

            # If metadata is available and the latest revision matches, skip to the next dataset.
            if dataset.updated_at and modification_date <= dataset.updated_at and size == dataset.update_size:
                self.stdout.write('Unchanged. Moving on.')
                # Record that the remote update check occurred.
                dataset.save(update_fields=['checked_at'])
                continue

            self.stdout.write('Downloading file modified on %s (%d bytes)...'
                              % (modification_date.strftime('%d-%b-%Y %H:%M'), size))
            try:
                archive = Archive.instance(transport.get_content(), os.path.basename(dataset.update_uri))
            except TransportError as error:
                self.stderr.write('Download failed: %s' % error.message)
                continue

            raw_format = models.Format.objects.get(name='Raw')
            for member_name in archive:
                file_, _ = models.File.objects.filter(dataset=dataset).get_or_create(
                    name=member_name, defaults={'dataset': dataset, 'default_format': raw_format})
                latest_revision = file_.revisions.first()
                latest_revision_number = latest_revision.level if latest_revision is not None else 0

                member = archive[member_name]
                try:
                    with transaction.atomic():
                        new_revision = models.Revision.objects.create(level=latest_revision_number + 1, file=file_,
                                                                      format=file_.default_format,
                                                                      size=member.size,
                                                                      updated_at=member.mtime or modification_date)

                        filename = self._get_path(new_revision)
                        path = os.path.dirname(filename)
                        if not os.path.exists(path):
                            os.makedirs(path)

                        # Decode previous file to raw
                        fp = member.data
                        preceding_revision = new_revision.get_previous()
                        if preceding_revision:
                            preceding_file = self._decode_chain(preceding_revision)
                            chain_args = (preceding_revision.level, preceding_file)
                        else:
                            preceding_file = None
                            chain_args = ()

                        # Decode next file to raw
                        next_revision = new_revision.get_next()
                        if next_revision:
                            next_file = self._decode_chain(next_revision, *chain_args)

                            # Recode next file using raw self
                            with xdelta.DeltaFile(open(self._get_path(next_revision), 'wb')) as delta:
                                delta.source = fp
                                while True:
                                    chunk = next_file.read(8 * 1024 * 1024)
                                    if not chunk:
                                        break
                                    delta.write(chunk)
                            # zipfile provides a read-only, unseekable file object, therefore re-open the file instead
                            # of rewinding to the beginning.
                            if not isinstance(archive, ZipArchive):
                                fp.seek(0)
                            else:
                                member = archive[member_name]
                                fp = member.data
                            # Delete next raw
                            del next_file

                        # Encode self using previous raw
                        with xdelta.DeltaFile(open(filename, 'wb')) as delta:
                            os.fchmod(delta.fileno(), stat.S_IWUSR | stat.S_IRUSR | stat.S_IRGRP | stat.S_IWGRP
                                                      | stat.S_IROTH)
                            delta.source = preceding_file
                            while True:
                                chunk = fp.read(8 * 1024 * 1024)
                                if not chunk:
                                    break
                                delta.write(chunk)
                except IOError as error:
                    if error.errno == errno.EACCES:
                        self.stderr.write("Cannot write to %s. Please check permissions." % error.filename)
                        continue

            dataset.updated_at = modification_date
            dataset.update_size = size if size != -1 else 0
            dataset.save()

        self.stdout.write('Updates complete.')

    @staticmethod
    def _get_path(revision):
        file_ = revision.file
        filename = '%s.%i.diff' % (sha1(file_.name).hexdigest(), revision.level)
        return os.path.join(app_settings.STORAGE_ROOT, file_.dataset.slug, filename)

    def _decode_chain(self, revision, start=-1, base=None):
        fp = base
        if revision:
            qs = models.Revision.objects.filter(file=revision.file)
            if start == -1:
                start = qs.first().level
            for rev in qs.filter(level__range=(revision.level, start)):
                path = self._get_path(rev)
                if not os.path.exists(path):
                    continue
                src = xdelta.DeltaFile(open(path, 'rb'))
                src.source = fp
                tgt = tempfile.TemporaryFile()
                for chunk in src.chunks():
                    tgt.write(chunk)
                src.close()
                fp = tgt
                fp.seek(0)
        return fp