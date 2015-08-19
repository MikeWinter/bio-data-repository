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

import io
import random
import string
from datetime import datetime
from django.test import TestCase
from bdr.backend import models
from bdr.utils import utc


class RevisionTest(TestCase):
    def tearDown(self):
        for dataset in models.Dataset.objects.all():
            dataset.delete()

    def test_instance_creation(self):
        revision = self.create_anonymous_revision()
        self.assertIsNotNone(revision)

    def test_reading_no_data_raises_exception(self):
        revision = self.create_anonymous_revision()
        with self.assertRaises(Exception):
            iterable = revision.data

    def test_writing_data_succeeds(self):
        revision = self.create_anonymous_revision()
        revision.data = io.BytesIO(self.create_random_content())

    def test_can_read_written_data(self):
        content = self.create_random_content()
        revision = self.create_anonymous_revision()
        revision.data = io.BytesIO(content)
        self.assertIn(content, revision.data)

    def test_adding_revision_extends_delta_chain(self):
        file_ = self.create_anonymous_file()
        rev1, rev1_content = self.create_revision(file_), self.create_random_content()
        rev1.data = io.BytesIO(rev1_content)

        rev2, rev2_content = self.create_revision(file_), self.create_random_content()
        rev2.data = io.BytesIO(rev2_content)

        rev3, rev3_content = self.create_revision(file_), self.create_random_content()
        rev3.data = io.BytesIO(rev3_content)

        # Obtain new Revision instances to force the reinitialisation of the data property
        self.assertEqual(self.get_revision(file_, 1).data.read(), rev1_content)
        self.assertEqual(self.get_revision(file_, 2).data.read(), rev2_content)
        self.assertEqual(self.get_revision(file_, 3).data.read(), rev3_content)

    def test_deleting_chain_head_recodes_next_revision(self):
        pass

    def test_deleting_chain_middle_recodes_next_revision(self):
        pass

    def test_can_delete_chain_tail(self):
        pass

    def create_anonymous_dataset(self):
        dataset = models.Dataset.objects.create(slug=str(random.randrange(1000)))
        return dataset

    def create_anonymous_file(self):
        last = models.File.objects.last()
        new_id = (last.id + 1) if last else 1
        name = "test{0}".format(new_id)
        dataset = self.create_anonymous_dataset()
        format_ = self.create_anonymous_format()
        file_ = models.File.objects.create(id=new_id, name=name, dataset=dataset, default_format=format_)
        return file_

    def create_anonymous_format(self):
        last = models.Format.objects.last()
        new_id = (last.id + 1) if last else 1
        name = "test{0}".format(new_id)
        format_ = models.Format.objects.create(id=new_id, name=name, slug=name)
        return format_

    def create_anonymous_revision(self):
        file_ = self.create_anonymous_file()
        return self.create_revision(file_)

    def create_revision(self, file_):
        last = models.Revision.objects.order_by('level').last()
        new_id = (last.id + 1) if last else 1
        timestamp = datetime.now(utc)
        revision = models.Revision.objects.create(file=file_, level=new_id, size=0, format=file_.default_format,
                                                  updated_at=timestamp)
        return revision

    def create_random_content(self, size=50):
        characters = string.letters
        return ''.join(random.choice(characters) for _ in range(size))

    def get_revision(self, file_, id):
        return models.Revision.objects.get(file=file_, level=id)