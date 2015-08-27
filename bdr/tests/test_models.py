from datetime import datetime, timedelta
import random
import string

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.test import TestCase

from .. import app_settings
from ..models import *
from bdr.utils.storage import upload_path
from ..utils import utc
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


class DatasetTest(TestCase):
    model = Dataset

    @classmethod
    def create_anonymous_dataset(cls):
        """
        :rtype: Dataset
        """
        name = _get_random_text()
        text = _get_random_text()
        return cls.model.objects.create(name=name, slug=name, notes=text)


class DataFileTest(TestCase):
    model = DataFile

    # def tearDown(self):
    #     self.model.objects.all().delete()

    # def test_add_revision_succeeds(self):
    #     file_ = self.create_anonymous_file()
    #     text = _get_random_text()
    #     revision = RevisionTest.create_revision(file_, data=text)
    #
    #     self.assertEqual(revision.number, 1)
    #     with revision.data as data:
    #         self.assertEqual(data.read(), text)

    @classmethod
    def create_anonymous_file(cls):
        """
        :rtype: DataFile
        """
        dataset = DatasetTest.create_anonymous_dataset()
        name = _get_random_text()
        return dataset.datafiles.create(name=name)


class RevisionTest(TestCase):
    model = Revision

    def tearDown(self):
        self.model.objects.all().delete()

    def test_revision_creation_succeeds(self):
        revision = self.create_anonymous_revision()

        self.assertEqual(revision.number, 1)

    def test_upload_path_creates_expected_pattern(self):
        filename = _get_random_text()
        revision = self.create_anonymous_revision()
        path = upload_path(revision, filename)

        self.assertRegexpMatches(path, r"^\d+[\\/][0-9a-f]+\.\d+$")

    def test_upload_path_fits_field(self):
        revision = self.create_anonymous_revision()
        filename = _get_random_text()
        path = upload_path(revision, filename)

        self.assertTrue(len(path) <= 100)

    def test_revision_numbers_are_sequential(self):
        datafile = DataFileTest.create_anonymous_file()
        count = 5

        revisions = self.create_revisions(datafile, count)

        self.assertListEqual([revision.number for revision in revisions], range(1, count + 1))

    def test_revision_numbers_are_independent(self):
        file1, file2 = DataFileTest.create_anonymous_file(), DataFileTest.create_anonymous_file()
        count = 5

        revisions1 = self.create_revisions(file1, count)
        revisions2 = self.create_revisions(file2, count)

        self.assertListEqual([revision.number for revision in revisions1], range(1, count + 1))
        self.assertListEqual([revision.number for revision in revisions2], range(1, count + 1))

    def test_deletion_affects_target_only(self):
        datafile = DataFileTest.create_anonymous_file()
        target = 3
        data = [_get_random_text() for _ in range(5)]
        self.create_revisions(datafile, data=data)
        del data[target - 1]

        datafile.revisions.get(number=target).delete()

        for revision, datum in zip(datafile.revisions.all(), data):
            with revision.data as stream:
                self.assertEqual(stream.read(), datum)

    def test_revision_numbers_are_sequential_in_sparse_revision_set(self):
        datafile = DataFileTest.create_anonymous_file()
        count = 5
        revisions = self.create_revisions(datafile, count)
        for _ in range(random.randrange(1, count - 1)):
            revision = random.choice(revisions)
            revision.delete()
            revisions.remove(revision)

        new_revision = self.create_revision(datafile)

        self.assertGreater(new_revision.number, revisions[-1].number)

    @classmethod
    def create_anonymous_revision(cls):
        """
        :rtype: Revision
        """
        datafile = DataFileTest.create_anonymous_file()
        return cls.create_revision(datafile)

    @classmethod
    def create_revision(cls, datafile, data=None, size=0, timestamp=None):
        """
        :rtype: Revision
        """
        if data is None:
            data = _get_random_text()
        if size == 0:
            size = len(data)
        if timestamp is None:
            timestamp = datetime.now(utc)
        return datafile.revisions.create(data=ContentFile(data, datafile.name), size=size,
                                         updated_at=timestamp)

    @classmethod
    def create_revisions(cls, datafile, count=0, data=None):
        """
        :rtype: list + Revision
        """
        if data is None:
            data = [None for _ in range(count)]
        return [cls.create_revision(datafile, datum) for datum in data]


class FilterTest(TestCase):
    model = Filter

    def test_valid_regex_validates(self):
        instance = self.create_filter(pattern="()")

        # A ValidationError exception is raised if validation fails here.
        instance.full_clean()

    def test_invalid_regex_raises_exception(self):
        instance = self.create_filter(pattern="(")

        with self.assertRaises(ValidationError):
            instance.full_clean()

    def test_valid_back_references_validate(self):
        instance = self.create_filter(pattern="()", mapping="\\1")

        # A ValidationError exception is raised if validation fails here.
        instance.full_clean()

    def test_invalid_back_references_raises_exception(self):
        # No group #2 exists in `pattern`
        instance = self.create_filter(pattern="()", mapping="\\1\\2")

        with self.assertRaises(ValidationError):
            instance.full_clean()

    def test_equal_pattern_matches(self):
        name = "test"
        instance = self.create_filter(pattern="^{0}$".format(name))

        self.assertTrue(instance.match(name))

    def test_non_equal_pattern_fails(self):
        name = "test"
        instance = self.create_filter(pattern="^bad-{0}$".format(name))

        self.assertFalse(instance.match(name))

    def test_inverted_equal_pattern_fails(self):
        name = "test"
        instance = self.create_filter(pattern="^{0}$".format(name), inverted=True)

        self.assertFalse(instance.match(name))

    def test_inverted_non_equal_pattern_matches(self):
        name = "test"
        instance = self.create_filter(pattern="^bad-{0}".format(name), inverted=True)

        self.assertTrue(instance.match(name))

    def test_empty_mapping_returns_unchanged(self):
        name = "test"
        instance = self.create_filter(pattern="^{0}$".format(name))

        self.assertEqual(instance.map(name), name)

    def test_mapping_succeeds(self):
        name = "test"
        result = "result"
        instance = self.create_filter(pattern="t(es)(t)", mapping="r\\1ul\\2")

        self.assertEqual(instance.map(name), result)

    def create_filter(self, pattern, inverted=False, mapping=""):
        source = SourceTest.create_source()
        return source.filters.create(pattern=pattern, inverted=inverted, mapping=mapping)


class SourceTest(TestCase):
    model = Source

    @classmethod
    def setUpClass(cls):
        app_settings.REMOTE_TRANSPORTS["mock"] = "bdr.tests.test_models.SourceTest.MockTransport"

    def test_update_check_fails_if_zero_frequency(self):
        source = self.create_source()

        self.assertFalse(source.has_update_elapsed())

    def test_update_check_fails_if_recent(self):
        timestamp = datetime.now(utc) - timedelta(minutes=59)
        source = self.create_source(checked_at=timestamp, frequency=1)

        self.assertFalse(source.has_update_elapsed())

    def test_update_check_succeeds_if_stale(self):
        timestamp = datetime.now(utc) - timedelta(minutes=60)
        source = self.create_source(checked_at=timestamp, frequency=1)

        self.assertTrue(source.has_update_elapsed())

    def test_mock(self):
        source = self.create_source()

        # self.assertEqual(source)

    @classmethod
    def create_source(cls, dataset=None, url="", frequency=0, checked_at=None):
        if dataset is None:
            dataset = DatasetTest.create_anonymous_dataset()
        return dataset.sources.create(url=url, checked_at=checked_at, frequency=frequency)

    class MockTransport(Transport):
        def get_size(self):
            return 5

        def get_modification_date(self):
            pass

        def _do_get_content(self):
            return "foo"


def _get_random_text(length=25):
    characters = string.letters
    return ''.join(random.choice(characters) for _ in range(length))
