"""
Tests for the bdr.models module.

This module has no public exports.
"""

from datetime import datetime, timedelta
import io
import random
import string

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.test import TestCase

from ..models import Dataset, File, Filter, Revision, Source, Update
from ..utils import utc
from ..utils.archives import Archive, Member
from ..utils.storage import upload_path
from ..utils.transports import Transport

__all__ = []
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


def create_dataset(cls=Dataset):
    """
    Create a Dataset instance with a random name, slug and note.

    :param cls: (Optional) The type of dataset to instantiate (default: `Dataset`).
    :type cls: Dataset
    :return: The constructed dataset.
    :rtype: Dataset
    """
    name = _get_random_text()
    text = _get_random_text()
    return cls.objects.create(name=name, notes=text)


def create_file(cls=File, dataset=None):
    """
    Create a File instance with a random name.

    :param cls: (Optional) The type of data file to instantiate (default:
                `File`).
    :type cls: File
    :param dataset: The dataset to which the new file is to be added. If None,
                    a new randomised dataset is created.
    :type dataset: Dataset
    :return: The constructed data file.
    :rtype: File
    """
    if dataset is None:
        dataset = create_dataset()
    name = _get_random_text()
    return cls.objects.create(dataset=dataset, name=name)


def create_revision(cls=Revision, datafile=None, data=None, size=0, update=None):
    """
    :rtype: Revision
    """
    if datafile is None:
        datafile = create_file()
    if data is None:
        data = _get_random_text()
    if size == 0:
        size = len(data)
    if update is None:
        update = create_update(dataset=datafile.dataset)
    return cls.objects.create(file=datafile, data=ContentFile(data, datafile.name), size=size,
                              update=update)


def create_revisions(cls=Revision, datafile=None, count=0, data=None):
    """
    :rtype: list of Revision
    """
    if datafile is None:
        datafile = create_file()
    if data is None:
        data = [None for _ in range(count)]
    dataset = datafile.dataset
    source = create_source(dataset=dataset)
    return [create_revision(cls, datafile, datum, update=create_update(dataset=dataset,
                                                                       source=source))
            for datum in data]


def create_source(cls=Source, dataset=None, url=None, period=0, checked_at=None):
    if dataset is None:
        dataset = create_dataset()
    if url is None:
        url = "http://example.local/{}".format(_get_random_text())
    return cls.objects.create(dataset=dataset, url=url, checked_at=checked_at,
                              period=period)


def create_filter(pattern, cls=Filter, source=None, inverted=False, mapping=""):
    if source is None:
        source = create_source()
    return cls.objects.create(source=source, pattern=pattern, inverted=inverted, mapping=mapping)


def create_update(cls=Update, dataset=None, source=None, timestamp=None, size=-1, modified_at=None):
    if dataset is None:
        dataset = create_dataset()
    if source is None:
        source = create_source(dataset=dataset)
    if timestamp is None:
        timestamp = datetime.now(utc)
    return cls.objects.create(dataset=dataset, source=source, timestamp=timestamp, size=size,
                              modified_at=modified_at)


class RevisionTest(TestCase):
    model = Revision

    def tearDown(self):
        self.model.objects.all().delete()

    def test_revision_creation_succeeds(self):
        revision = create_revision()

        self.assertEqual(revision.number, 1)

    def test_upload_path_creates_expected_pattern(self):
        filename = _get_random_text()
        revision = create_revision()
        path = upload_path(revision, filename)

        self.assertRegexpMatches(path, r"^\d+[\\/][0-9a-f]+\.\d+$")

    def test_upload_path_fits_field(self):
        revision = create_revision()
        filename = _get_random_text()
        path = upload_path(revision, filename)

        self.assertTrue(len(path) <= 100)

    def test_revision_numbers_are_sequential(self):
        count = 5

        revisions = create_revisions(count=count)

        self.assertListEqual([revision.number for revision in revisions], range(1, count + 1))

    def test_revision_numbers_are_independent(self):
        count = 5

        revisions1 = create_revisions(count=count)
        revisions2 = create_revisions(count=count)

        self.assertListEqual([revision.number for revision in revisions1], range(1, count + 1))
        self.assertListEqual([revision.number for revision in revisions2], range(1, count + 1))

    def test_deletion_affects_target_only(self):
        datafile = create_file()
        target = 3
        data = [_get_random_text() for _ in range(5)]
        create_revisions(datafile=datafile, data=data)
        del data[target - 1]

        datafile.revisions.get(number=target).delete()

        for revision, datum in zip(datafile.revisions.all(), data):
            with revision.data as stream:
                self.assertEqual(stream.read(), datum)

    def test_revision_numbers_are_sequential_in_sparse_revision_set(self):
        datafile = create_file()
        count = 5
        revisions = create_revisions(datafile=datafile, count=count)
        for _ in range(random.randrange(1, count - 1)):
            revision = random.choice(revisions)
            revision.delete()
            revisions.remove(revision)

        new_revision = create_revision(datafile=datafile)

        self.assertGreater(new_revision.number, revisions[-1].number)


class FilterTest(TestCase):
    def test_valid_regex_validates(self):
        instance = create_filter(pattern="()")

        # A ValidationError exception is raised if validation fails here.
        instance.full_clean()

    def test_invalid_regex_raises_exception(self):
        instance = create_filter(pattern="(")

        with self.assertRaises(ValidationError):
            instance.full_clean()

    def test_valid_back_references_validate(self):
        instance = create_filter(pattern="()", mapping="\\1")

        # A ValidationError exception is raised if validation fails here.
        instance.full_clean()

    def test_invalid_back_references_raises_exception(self):
        # No group #2 exists in `pattern`
        instance = create_filter(pattern="()", mapping="\\1\\2")

        with self.assertRaises(ValidationError):
            instance.full_clean()

    def test_equal_pattern_matches(self):
        name = "test"
        instance = create_filter(pattern="^{0}$".format(name))

        self.assertTrue(instance.match(name))

    def test_non_equal_pattern_fails(self):
        name = "test"
        instance = create_filter(pattern="^bad-{0}$".format(name))

        self.assertFalse(instance.match(name))

    def test_inverted_equal_pattern_fails(self):
        name = "test"
        instance = create_filter(pattern="^{0}$".format(name), inverted=True)

        self.assertFalse(instance.match(name))

    def test_inverted_non_equal_pattern_matches(self):
        name = "test"
        instance = create_filter(pattern="^bad-{0}".format(name), inverted=True)

        self.assertTrue(instance.match(name))

    def test_empty_mapping_returns_unchanged(self):
        name = "test"
        instance = create_filter(pattern="^{0}$".format(name))

        self.assertEqual(instance.map(name), name)

    def test_mapping_succeeds(self):
        name = "test"
        result = "result"
        instance = create_filter(pattern="t(es)(t)", mapping="r\\1ul\\2")

        self.assertEqual(instance.map(name), result)


class SourceTest(TestCase):
    def test_update_check_fails_if_zero_frequency(self):
        source = create_source()

        self.assertFalse(source.has_update_elapsed())

    def test_update_check_succeeds_if_never_checked(self):
        source = create_source(period=1)

        self.assertTrue(source.has_update_elapsed())

    def test_update_check_fails_if_recent(self):
        timestamp = datetime.now(utc) - timedelta(minutes=59)
        source = create_source(checked_at=timestamp, period=1)

        self.assertFalse(source.has_update_elapsed())

    def test_update_check_succeeds_if_stale(self):
        timestamp = datetime.now(utc) - timedelta(minutes=60)
        source = create_source(checked_at=timestamp, period=1)

        self.assertTrue(source.has_update_elapsed())

    def test_update_check_fails_after_checked(self):
        source = create_source(period=1)

        source.checked()

        self.assertFalse(source.has_update_elapsed())

    def test_has_changed_if_no_existing_updates(self):
        source = create_source()

        def _transport_factory(url, user, password):
            return FakeTransport(url, user, password)
        source.transport_provider_factory = _transport_factory

        self.assertEqual(source.updates.count(), 0)
        self.assertTrue(source.has_changed())

    def test_has_changed_if_state_unknown(self):
        update = create_update()
        source = update.source

        def _transport_factory(url, user, password):
            return FakeTransport(url, user, password)
        source.transport_provider_factory = _transport_factory

        self.assertTrue(source.has_changed())

    def test_has_changed_if_updates_stale(self):
        modification_date = datetime.now(utc)
        last_updated_at = modification_date - timedelta(days=1)
        update = create_update(modified_at=last_updated_at)
        source = update.source

        def _transport_factory(url, user, password):
            return FakeTransport(url, user, password, m_date=modification_date)
        source.transport_provider_factory = _transport_factory

        self.assertTrue(source.has_changed())

    def test_unchanged_if_updates_fresh(self):
        modification_date = datetime.now(utc)
        last_updated_at = modification_date + timedelta(days=1)
        update = create_update(modified_at=last_updated_at)
        source = update.source

        def _transport_factory(url, user, password):
            return FakeTransport(url, user, password, m_date=modification_date)
        source.transport_provider_factory = _transport_factory

        self.assertFalse(source.has_changed())

    def test_has_changed_if_size_different(self):
        current_size = 1024
        new_size = 2048
        update = create_update(size=current_size)
        source = update.source

        def _transport_factory(url, user, password):
            return FakeTransport(url, user, password, size=new_size)
        source.transport_provider_factory = _transport_factory

        self.assertTrue(source.has_changed())

    def test_no_filters_returns_files(self):
        update = create_update()
        source = update.source
        file_names = [_get_random_text() for _ in range(5)]
        expected_files = file_names[:]

        def _transport_factory(url, user, password):
            return FakeTransport(url, user, password)
        source.transport_provider_factory = _transport_factory

        def _archive_factory(archive_file, path):
            return FakeArchive(archive_file, path, file_names)
        source.archive_factory = _archive_factory

        files, _, _ = source.files()
        self.assertListEqual([file.name for file in files], expected_files)

    def test_no_matching_files_returns_empty_list(self):
        update = create_update()
        source = update.source
        file_names = [_get_random_text() for _ in range(5)]
        create_filter("^accepted$", source=source)
        expected_files = []

        def _transport_factory(url, user, password):
            return FakeTransport(url, user, password)
        source.transport_provider_factory = _transport_factory

        def _archive_factory(archive_file, path):
            return FakeArchive(archive_file, path, file_names)
        source.archive_factory = _archive_factory

        files, _, _ = source.files()
        self.assertListEqual(files, expected_files)

    def test_matching_files_returns_mapped_list(self):
        update = create_update()
        source = update.source
        file_names = [_get_random_text() for _ in range(5)]
        create_filter("^(.+)$", mapping="accepted-\\1", source=source)
        expected_files = ["accepted-{}".format(name) for name in file_names]

        def _transport_factory(url, user, password):
            return FakeTransport(url, user, password)
        source.transport_provider_factory = _transport_factory

        def _archive_factory(archive_file, path):
            return FakeArchive(archive_file, path, file_names)
        source.archive_factory = _archive_factory

        files, _, _ = source.files()
        self.assertListEqual([file.name for file in files], expected_files)


class FakeArchive(Archive):
    """
    A fake subclass of the abstract Archive class that does nothing.
    """
    def __init__(self, archive_file, path=None, names=None):
        """
        Create an archive, reading the specified file.

        :param archive_file: A file-like object containing an archive.
        :type archive_file:  file
        :param path: The absolute path of the archive.
        :type path:  str
        :param names: (Optional) A list of names in this archive.
        :type names: list of str
        """
        super(FakeArchive, self).__init__(archive_file, path)
        self.names = names if names is not None else []

    def keys(self):
        return self.names

    def can_read(self):
        return True

    def __getitem__(self, key):
        """
        Return a Member instance describing a file within the archive.

        :param key: The name of the file to be retrieved.
        :type key: str
        :return: The file member named by `key`.
        :rtype:  Member
        """
        return Member(key, 0, None, None)


class FakeTransport(Transport):
    """
    A fake subclass of the abstract Transport class that does nothing.
    """

    def __init__(self, url, user, password, size=-1, m_date=None):
        """
        Create an instance of a data transport mechanism.

        :param url: The URL of the resource to be obtained.
        :type  url: str
        :param user: The user name required to access the resource specified in
                     `url` (optional).
        :type  user: str
        :param password: The password required to access the resource specified
                         in `url` (optional).
        :type  password: str
        """
        super(FakeTransport, self).__init__(url, user, password)
        self.size = size
        self.m_date = m_date

    def get_size(self):
        """
        Return the size of this resource.

        :return: The size (in bytes) of this resource, or -1 if unknown.
        :rtype:  int
        """
        return self.size

    def get_modification_date(self):
        """
        Return the date and time of the last modification to this resource.

        :return: The modification date and time, or None if unknown.
        :rtype:  datetime | None
        """
        return self.m_date

    def _do_get_content(self):
        return io.BytesIO()


def _get_random_text(length=25):
    characters = string.letters
    return ''.join(random.choice(characters) for _ in range(length))
