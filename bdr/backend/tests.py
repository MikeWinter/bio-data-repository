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

from datetime import datetime
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse
from django.test import TestCase

from . import models
from ..utils import utc


class TagDetailViewTest(TestCase):
    def setUp(self):
        """Define basic model objects for use during fixtures."""
        self.ENCODER = DjangoJSONEncoder()
        self.DATASET = models.Dataset.objects.create(name='Test', slug='test')
        self.FORMAT = models.Format.objects.get(slug='raw')
        self.FILE = models.File.objects.create(name='example.txt', dataset=self.DATASET, default_format=self.FORMAT)
        self.REVISION = models.Revision.objects.create(file=self.FILE, level=1, size=1000, format=self.FORMAT,
                                                       updated_at=datetime.now(utc))
        self.CATEGORY = models.Category.objects.create(name='Example', slug='example')
        self.DATASET.categories.add(self.CATEGORY)

    def test_non_existent_tag_returns_404(self):
        """Ensure that a 404 HTTP response code is returned if no tag matches a given identifier."""
        response = self.client.head(reverse('bdr.backend:tag-detail', kwargs={'pk': 1}))
        self.assertEqual(404, response.status_code)

    def test_head_returns_200(self):
        """Ensure that a request for a matched identifier returns a 200 HTTP response code."""
        pk, name = 1, 'test'
        models.Tag.objects.create(id=pk, name=name)

        response = self.client.head(reverse('bdr.backend:tag-detail', kwargs={'pk': pk}))
        self.assertEqual(200, response.status_code)

    def test_get_returns_basic_data(self):
        """Check that, with a valid identifier, basic fields are populated and match the API format."""
        pk, name = 1, 'test'
        models.Tag.objects.create(id=pk, name=name)

        url = reverse('bdr.backend:tag-detail', kwargs={'pk': pk})
        response = self.client.get(url)
        self.assertJSONEqual(response.content,
                             {'name': name, 'href': url, 'datasets': [], 'files': [], 'revisions': []})

    def test_get_includes_dataset_reference(self):
        """Ensure that a tagged dataset can be referenced correctly in the response."""
        pk, name = 1, 'test'
        tag = models.Tag.objects.create(id=pk, name=name)
        self.DATASET.tags.add(tag)

        url = reverse('bdr.backend:tag-detail', kwargs={'pk': pk})
        response = self.client.get(url)
        self.assertJSONEqual(response.content,
                             {'name': name,
                              'href': url,
                              'datasets': [{'name': self.DATASET.name,
                                            'href': self.DATASET.get_absolute_url(),
                                            'slug': self.DATASET.slug,
                                            'files': 1,
                                            'categories': [{'name': self.CATEGORY.name,
                                                            'href': self.CATEGORY.get_absolute_url(),
                                                            'slug': self.CATEGORY.slug,
                                                            'parent': None}],
                                            'tags': [{'name': name, 'href': tag.get_absolute_url()}]}],
                              'files': [],
                              'revisions': []})

    def test_get_includes_dataset_references(self):
        """Ensure that multiple datasets can be referenced correctly in the response."""
        pk, name = 1, 'test'
        tag = models.Tag.objects.create(id=pk, name=name)
        self.DATASET.tags.add(tag)

        another_dataset = models.Dataset.objects.create(name='Test-2', slug='test-2')
        another_dataset.tags.add(tag)

        url = reverse('bdr.backend:tag-detail', kwargs={'pk': pk})
        response = self.client.get(url)
        self.assertJSONEqual(response.content,
                             {'name': name,
                              'href': url,
                              'datasets': [
                                  {'name': self.DATASET.name,
                                   'href': self.DATASET.get_absolute_url(),
                                   'slug': self.DATASET.slug,
                                   'files': models.File.objects.filter(dataset=self.DATASET).count(),
                                   'categories': [
                                       {'name': self.CATEGORY.name,
                                        'href': self.CATEGORY.get_absolute_url(),
                                        'slug': self.CATEGORY.slug,
                                        'parent': None}],
                                   'tags': [{'name': name, 'href': tag.get_absolute_url()}]},
                                  {'name': another_dataset.name,
                                   'href': another_dataset.get_absolute_url(),
                                   'slug': another_dataset.slug,
                                   'files': models.File.objects.filter(dataset=another_dataset).count(),
                                   'categories': [],
                                   'tags': [{'name': name, 'href': tag.get_absolute_url()}]}],
                              'files': [],
                              'revisions': []})

    def test_get_includes_file_reference(self):
        """Ensure that a tagged file can be referenced correctly in the response."""
        pk, name = 1, 'test'
        tag = models.Tag.objects.create(id=pk, name=name)
        self.FILE.tags.add(tag)

        url = reverse('bdr.backend:tag-detail', kwargs={'pk': pk})
        response = self.client.get(url)
        self.assertJSONEqual(response.content,
                             {'name': name,
                              'href': url,
                              'datasets': [],
                              'files': [{'name': self.FILE.name,
                                         'href': self.FILE.get_absolute_url(),
                                         'default_format': self.FORMAT.get_absolute_url(),
                                         'revisions': 1,
                                         'tags': [{'name': name, 'href': tag.get_absolute_url()}]}],
                              'revisions': []})

    def test_get_includes_revision_reference(self):
        """Ensure that a tagged revision can be referenced correctly in the response."""
        pk, name = 1, 'test'
        tag = models.Tag.objects.create(id=pk, name=name)
        self.REVISION.tags.add(tag)

        url = reverse('bdr.backend:tag-detail', kwargs={'pk': pk})
        response = self.client.get(url)
        self.assertJSONEqual(response.content,
                             {'name': name,
                              'href': url,
                              'datasets': [],
                              'files': [],
                              'revisions': [{'revision': self.REVISION.level,
                                             'href': self.REVISION.get_absolute_url(),
                                             'format': self.REVISION.format.get_absolute_url(),
                                             'size': self.REVISION.size,
                                             'updated_at': self.ENCODER.default(self.REVISION.updated_at),
                                             'tags': [{'name': name, 'href': tag.get_absolute_url()}]}]})


class TagCollectionViewTest(TestCase):
    def test_collection_returns_200(self):
        """Ensure that this collection view always succeeds, even if there are no registered tags."""
        response = self.client.get(reverse('bdr.backend:tags'))
        self.assertEquals(200, response.status_code)

    def test_no_tags_returns_empty_list(self):
        """Check that the tag collection is an empty list when no tags have been created."""
        response = self.client.get(reverse('bdr.backend:tags'))
        self.assertJSONEqual(response.content, {'tags': []})

    def test_returns_tag_reference(self):
        """Check that tag references match the API format."""
        name = 'test'
        tag = models.Tag.objects.create(name=name)

        response = self.client.get(reverse('bdr.backend:tags'))
        self.assertJSONEqual(response.content, {'tags': [{'name': name, 'href': tag.get_absolute_url()}]})

    def test_returns_sorted_tag_references(self):
        """Ensure that tags are sorted by name."""
        names = ['foo', 'bar']
        tags = {name: models.Tag.objects.create(name=name) for name in names}

        response = self.client.get(reverse('bdr.backend:tags'))
        self.assertJSONEqual(response.content,
                             {'tags': [{'name': tags[name].name,
                                        'href': tags[name].get_absolute_url()}
                                       for name in sorted(names)]})


class CategoryDetailViewTest(TestCase):
    def setUp(self):
        """Define basic model objects for use during fixtures."""
        self.DATASET = models.Dataset.objects.create(name='Test', slug='test')

    def test_non_existent_category_returns_404(self):
        """Ensure that a 404 HTTP response code is returned if no category matches a given identifier."""
        response = self.client.head(reverse('bdr.backend:category-detail', kwargs={'slug': 'missing'}))
        self.assertEqual(404, response.status_code)

    def test_head_returns_200(self):
        """Ensure that a request for a matched identifier returns a 200 HTTP response code."""
        name, slug = 'Test', 'slug'
        models.Category.objects.create(name=name, slug=slug)

        response = self.client.head(reverse('bdr.backend:category-detail', kwargs={'slug': slug}))
        self.assertEqual(200, response.status_code)

    def test_get_returns_basic_data(self):
        """Check that, with a valid identifier, basic fields are populated and match the API format."""
        name, slug = 'Test', 'test'
        models.Category.objects.create(name=name, slug=slug)

        url = reverse('bdr.backend:category-detail', kwargs={'slug': slug})
        response = self.client.get(url)
        self.assertJSONEqual(response.content,
                             {'name': name, 'href': url, 'slug': slug, 'parent': None, 'subcategories': [],
                              'datasets': []})

    def test_get_includes_parent_reference(self):
        """Check that a subcategory correctly includes a reference to its parent category."""
        parent, child = [models.Category.objects.create(name=name, slug=name) for name in ['parent', 'child']]
        parent.subcategories.add(child)

        url = reverse('bdr.backend:category-detail', kwargs={'slug': child.slug})
        response = self.client.get(url)
        self.assertJSONEqual(response.content,
                             {'name': child.name, 'href': url, 'slug': child.name, 'parent': parent.get_absolute_url(),
                              'subcategories': [], 'datasets': []})

    def test_get_includes_child_reference(self):
        """Ensure that a category includes references to child categories."""
        parent, child = [models.Category.objects.create(name=name, slug=name) for name in ['parent', 'child']]
        parent.subcategories.add(child)

        url = reverse('bdr.backend:category-detail', kwargs={'slug': parent.name})
        response = self.client.get(url)
        self.assertJSONEqual(response.content,
                             {'name': parent.name, 'href': url, 'slug': parent.name, 'parent': None,
                              'subcategories': [{'name': child.name, 'href': child.get_absolute_url(),
                                                 'slug': child.name, 'parent': url}],
                              'datasets': []})

    def test_get_includes_dataset_reference(self):
        """Ensure that a categorised dataset can be referenced correctly in the response."""
        name, slug = 'Test', 'test'
        category = models.Category.objects.create(name=name, slug=slug)
        self.DATASET.categories.add(category)

        url = reverse('bdr.backend:category-detail', kwargs={'slug': slug})
        response = self.client.get(url)
        self.assertJSONEqual(response.content,
                             {'name': name,
                              'href': url,
                              'slug': slug,
                              'parent': None,
                              'subcategories': [],
                              'datasets': [{'name': self.DATASET.name,
                                            'href': self.DATASET.get_absolute_url(),
                                            'slug': self.DATASET.slug,
                                            'files': 0,
                                            'categories': [{'name': category.name,
                                                            'href': category.get_absolute_url(),
                                                            'slug': category.slug,
                                                            'parent': None}],
                                            'tags': []}]})


class CategoryCollectionViewTest(TestCase):
    def test_collection_returns_200(self):
        """Ensure that this collection view always succeeds, even if there are no registered categories."""
        response = self.client.get(reverse('bdr.backend:categories'))
        self.assertEquals(200, response.status_code)

    def test_no_categories_returns_empty_list(self):
        """Check that the category collection is an empty list when no categories have been created."""
        response = self.client.get(reverse('bdr.backend:categories'))
        self.assertJSONEqual(response.content, {'categories': []})

    def test_returns_category_reference(self):
        """Check that category references match the API format."""
        name, slug = 'Test', 'test'
        category = models.Category.objects.create(name=name, slug=slug)
        category.save()

        response = self.client.get(reverse('bdr.backend:categories'))
        self.assertJSONEqual(response.content, {'categories': [{'name': name, 'href': category.get_absolute_url(),
                                                                'slug': slug, 'parent': None}]})

    def test_returns_sorted_category_references(self):
        """Ensure that categories are sorted by name."""
        names = ['foo', 'bar']
        categories = {name: models.Category.objects.create(name=name, slug=name) for name in names}

        response = self.client.get(reverse('bdr.backend:categories'))
        self.assertJSONEqual(response.content,
                             {'categories': [{'name': categories[name].name,
                                              'href': categories[name].get_absolute_url(),
                                              'slug': categories[name].slug,
                                              'parent': None}
                                             for name in sorted(names)]})

    def test_returns_hierarchical_category_references(self):
        """Ensure that category references include parent/child references."""
        names = ['child', 'sibling', 'parent']
        categories = {name: models.Category.objects.create(name=name, slug=name) for name in names}
        categories['parent'].subcategories.add(categories['child'])

        response = self.client.get(reverse('bdr.backend:categories'))
        expected_order = ['parent', 'child', 'sibling']
        self.assertJSONEqual(response.content,
                             {'categories': [{'name': categories[name].name,
                                              'href': categories[name].get_absolute_url(),
                                              'slug': categories[name].slug,
                                              'parent': (categories[name].parent
                                                         and categories[name].parent.get_absolute_url())}
                                             for name in expected_order]})


class DatasetDetailViewTest(TestCase):
    def setUp(self):
        self.ENCODER = DjangoJSONEncoder()
        self.DATASET = models.Dataset.objects.create(name='Test', slug='test', updated_at=datetime.now(utc))
        self.FORMAT = models.Format.objects.get(slug='raw')
        self.CATEGORY = models.Category.objects.create(name='Example', slug='example')
        self.TAG = models.Tag.objects.create(name='testing')

    def test_non_existent_dataset_returns_404(self):
        """Ensure that a 404 HTTP response code is returned if no dataset matches a given identifier."""
        response = self.client.head(reverse('bdr.backend:dataset-detail', kwargs={'slug': 'missing'}))
        self.assertEqual(404, response.status_code)

    def test_head_returns_200(self):
        """Ensure that a request for a matched identifier returns a 200 HTTP response code."""
        response = self.client.head(reverse('bdr.backend:dataset-detail', kwargs={'slug': self.DATASET.slug}))
        self.assertEqual(200, response.status_code)

    def test_get_returns_basic_data(self):
        """Check that, with a valid identifier, basic fields are populated and match the API format."""
        slug = self.DATASET.slug
        url = reverse('bdr.backend:dataset-detail', kwargs={'slug': slug})
        response = self.client.get(url)
        self.assertJSONEqual(response.content,
                             {'name': self.DATASET.name, 'href': url, 'slug': slug, 'notes': '', 'categories': [],
                              'tags': [], 'update_uri': '', 'update_frequency': 0, 'update_username': '',
                              'update_password': '', 'updated_at': self.ENCODER.default(self.DATASET.updated_at),
                              'files': []})

    def test_get_includes_category_reference(self):
        """Check that category references match the API format."""
        self.DATASET.categories.add(self.CATEGORY)

        slug = self.DATASET.slug
        url = reverse('bdr.backend:dataset-detail', kwargs={'slug': slug})
        response = self.client.get(url)
        self.assertJSONEqual(response.content,
                             {'name': self.DATASET.name, 'href': url, 'slug': slug, 'notes': '',
                              'categories': [{'name': self.CATEGORY.name,
                                              'href': self.CATEGORY.get_absolute_url(),
                                              'slug': self.CATEGORY.slug,
                                              'parent': None}],
                              'tags': [], 'update_uri': '', 'update_frequency': 0, 'update_username': '',
                              'update_password': '', 'updated_at': self.ENCODER.default(self.DATASET.updated_at),
                              'files': []})

    def test_get_includes_tag_reference(self):
        """Check that tag references match the API format."""
        self.DATASET.tags.add(self.TAG)

        slug = self.DATASET.slug
        url = reverse('bdr.backend:dataset-detail', kwargs={'slug': slug})
        response = self.client.get(url)
        self.assertJSONEqual(response.content,
                             {'name': self.DATASET.name, 'href': url, 'slug': slug, 'notes': '', 'categories': [],
                              'tags': [{'name': self.TAG.name, 'href': self.TAG.get_absolute_url()}],
                              'update_uri': '', 'update_frequency': 0, 'update_username': '', 'update_password': '',
                              'updated_at': self.ENCODER.default(self.DATASET.updated_at), 'files': []})

    def test_get_includes_file_references(self):
        """Check that file references match the API format."""
        files = [models.File.objects.create(name=name, dataset=self.DATASET, default_format=self.FORMAT)
                 for name in sorted(['foo', 'bar'])]
        for f in files:
            self.DATASET.files.add(f)

        slug = self.DATASET.slug
        url = reverse('bdr.backend:dataset-detail', kwargs={'slug': slug})
        response = self.client.get(url)
        self.assertJSONEqual(response.content,
                             {'name': self.DATASET.name, 'href': url, 'slug': slug, 'notes': '', 'categories': [],
                              'tags': [], 'update_uri': '', 'update_frequency': 0, 'update_username': '',
                              'update_password': '', 'updated_at': self.ENCODER.default(self.DATASET.updated_at),
                              'files': [{'name': f.name,
                                         'href': f.get_absolute_url(),
                                         'default_format': self.FORMAT.get_absolute_url(),
                                         'revisions': 0,
                                         'tags': []}
                                        for f in files]})

    def test_put_changes_details(self):
        slug = self.DATASET.slug
        data = {'name': 'foo', 'slug': slug, 'notes': 'This is a test!', 'update_uri': 'http://www.example.com/',
                'update_frequency': 10, 'update_username': '', 'update_password': '', 'categories': [], 'tags': []}

        url = reverse('bdr.backend:dataset-detail', kwargs={'slug': slug})
        response = self.client.put(url, json.dumps(data), 'application/json', follow=True)
        self.assertEqual(response.status_code, 200)

        new_data = dict(updated_at=self.ENCODER.default(models.Dataset.objects.get(slug=slug).updated_at), files=[],
                        href=url, **data)
        self.assertJSONEqual(response.content, new_data)

    def test_put_sets_categories(self):
        slug = self.DATASET.slug
        data = {'name': self.DATASET.name, 'slug': slug, 'notes': self.DATASET.notes,
                'update_uri': self.DATASET.update_uri, 'update_frequency': self.DATASET.update_frequency,
                'update_username': '', 'update_password': '', 'categories': [self.CATEGORY.get_absolute_url()],
                'tags': []}

        url = reverse('bdr.backend:dataset-detail', kwargs={'slug': slug})
        response = self.client.put(url, json.dumps(data), 'application/json', follow=True)
        self.assertEqual(response.status_code, 200)

        new_data = dict(updated_at=self.ENCODER.default(models.Dataset.objects.get(slug=slug).updated_at), files=[],
                        href=url, **data)
        new_data['categories'][0] = {'href': self.CATEGORY.get_absolute_url(), 'name': self.CATEGORY.name,
                                     'parent': self.CATEGORY.parent, 'slug': self.CATEGORY.slug}
        self.assertJSONEqual(response.content, new_data)


class DatasetCollectionViewTest(TestCase):
    def test_collection_returns_200(self):
        """Ensure that this collection view always succeeds, even if there are no datasets."""
        response = self.client.get(reverse('bdr.backend:datasets'))
        self.assertEquals(200, response.status_code)

    def test_no_datasets_returns_empty_list(self):
        """Check that the dataset collection is an empty list when no datasets have been added."""
        response = self.client.get(reverse('bdr.backend:datasets'))
        self.assertJSONEqual(response.content, {'datasets': []})

    def test_returns_dataset_reference(self):
        """Check that dataset references match the API format."""
        name, slug = 'Test', 'test'
        dataset = models.Dataset.objects.create(name=name, slug=slug)

        url = reverse('bdr.backend:datasets')
        response = self.client.get(url)
        self.assertJSONEqual(response.content, {'datasets': [{'name': name, 'href': dataset.get_absolute_url(),
                                                              'slug': slug, 'files': 0, 'categories': [], 'tags': []}]})

    def test_includes_file_count(self):
        """Check that dataset references includes an accurate file count."""
        from random import randint
        name, slug = 'Test', 'slug'
        dataset = models.Dataset.objects.create(name=name, slug=slug)
        file_format = models.Format.objects.get(slug='raw')
        file_count = randint(1, 10)
        for i in range(1, file_count + 1):
            models.File.objects.create(name='example%s.txt' % i, dataset=dataset, default_format=file_format)

        url = reverse('bdr.backend:datasets')
        response = self.client.get(url)
        self.assertJSONEqual(response.content, {'datasets': [{'name': name, 'href': dataset.get_absolute_url(),
                                                              'slug': slug, 'files': file_count, 'categories': [],
                                                              'tags': []}]})

    def test_includes_category_reference(self):
        """Check that category references match the API format."""
        name, slug = 'Test', 'test'
        dataset = models.Dataset.objects.create(name=name, slug=slug)
        category = models.Category.objects.create(name='Example', slug='example')
        dataset.categories.add(category)

        response = self.client.get(reverse('bdr.backend:datasets'))
        self.assertJSONEqual(response.content, {'datasets': [{'name': name, 'href': dataset.get_absolute_url(),
                                                              'slug': slug, 'files': 0,
                                                              'categories': [{'name': category.name,
                                                                              'href': category.get_absolute_url(),
                                                                              'slug': category.slug,
                                                                              'parent': None}],
                                                              'tags': []}]})

    def test_includes_tag_reference(self):
        """Check that tag references match the API format."""
        name, slug = 'Test', 'test'
        dataset = models.Dataset.objects.create(name=name, slug=slug)
        tag = models.Tag.objects.create(name='Example')
        dataset.tags.add(tag)

        response = self.client.get(reverse('bdr.backend:datasets'))
        self.assertJSONEqual(response.content, {'datasets': [{'name': name, 'href': dataset.get_absolute_url(),
                                                              'slug': slug, 'files': 0, 'categories': [],
                                                              'tags': [{'name': tag.name,
                                                                        'href': tag.get_absolute_url()}]}]})


class FileDetailViewTest(TestCase):
    def setUp(self):
        self.ENCODER = DjangoJSONEncoder()
        self.DATASET = models.Dataset.objects.create(name='Test', slug='test')
        self.FORMAT = models.Format.objects.get(slug='raw')
        self.FILE = models.File.objects.create(name='example.txt', dataset=self.DATASET, default_format=self.FORMAT)
        self.CATEGORY = models.Category.objects.create(name='Example')
        self.TAG = models.Tag.objects.create(name='testing')

    def test_non_existent_dataset_returns_404(self):
        """Ensure that a 404 HTTP response code is returned if no dataset matches a given identifier."""
        response = self.client.head(reverse('bdr.backend:file-detail', kwargs={'ds': 'missing', 'fn': 'missing'}))
        self.assertEqual(404, response.status_code)

    def test_non_existent_file_returns_404(self):
        """Ensure that a 404 HTTP response code is returned if no file matches a given identifier."""
        response = self.client.head(reverse('bdr.backend:file-detail', kwargs={'ds': self.DATASET.slug,
                                                                               'fn': 'missing'}))
        self.assertEqual(404, response.status_code)

    def test_head_returns_200(self):
        """Ensure that a request for a matched identifier returns a 200 HTTP response code."""
        response = self.client.head(reverse('bdr.backend:file-detail', kwargs={'ds': self.DATASET.slug,
                                                                               'fn': self.FILE.name}))
        self.assertEqual(200, response.status_code)

    def test_get_returns_basic_data(self):
        """Check that, with a valid identifier, basic fields are populated and match the API format."""
        url = reverse('bdr.backend:file-detail', kwargs={'ds': self.DATASET.slug, 'fn': self.FILE.name})
        response = self.client.get(url)
        self.assertJSONEqual(response.content,
                             {'name': self.FILE.name, 'href': url, 'default_format': self.FORMAT.get_absolute_url(),
                              'tags': [], 'revisions': []})

    def test_get_includes_tag_reference(self):
        """Check that tag references match the API format."""
        self.FILE.tags.add(self.TAG)

        url = reverse('bdr.backend:file-detail', kwargs={'ds': self.DATASET.slug, 'fn': self.FILE.name})
        response = self.client.get(url)
        self.assertJSONEqual(response.content,
                             {'name': self.FILE.name, 'href': url, 'default_format': self.FORMAT.get_absolute_url(),
                              'tags': [{'name': self.TAG.name, 'href': self.TAG.get_absolute_url()}], 'revisions': []})

    def test_get_includes_revision_references(self):
        """Check that revision references match the API format."""
        revisions = [models.Revision.objects.create(level=level, file=self.FILE, size=0, format=self.FORMAT,
                                                    updated_at=datetime.now(utc))
                     for level in range(1, 3)]
        for r in revisions:
            self.FILE.revisions.add(r)

        url = reverse('bdr.backend:file-detail', kwargs={'ds': self.DATASET.slug, 'fn': self.FILE.name})
        response = self.client.get(url)
        self.assertJSONEqual(response.content,
                             {'name': self.FILE.name, 'href': url, 'default_format': self.FORMAT.get_absolute_url(),
                              'tags': [],
                              'revisions': [{'revision': r.level,
                                             'href': r.get_absolute_url(),
                                             'format': r.format.get_absolute_url(),
                                             'size': 0,
                                             'updated_at': self.ENCODER.default(r.updated_at),
                                             'tags': []}
                                            for r in reversed(revisions)]})


class FileCollectionViewTest(TestCase):
    def setUp(self):
        self.DATASET = models.Dataset.objects.create(name='Test', slug='test')
        self.FORMAT = models.Format.objects.get(slug='raw')

    def test_collection_returns_200(self):
        """Ensure that this collection view always succeeds, even if there are no files."""
        response = self.client.get(reverse('bdr.backend:dataset-files', kwargs={'ds': self.DATASET.slug}))
        self.assertEquals(200, response.status_code)

    def test_no_files_returns_empty_list(self):
        """Check that the file collection is an empty list when no files have been added."""
        response = self.client.get(reverse('bdr.backend:dataset-files', kwargs={'ds': self.DATASET.slug}))
        self.assertJSONEqual(response.content, {'files': []})

    def test_returns_file_reference(self):
        """Check that file references match the API format."""
        name = 'example.txt'
        file_obj = models.File.objects.create(name=name, default_format=self.FORMAT, dataset=self.DATASET)

        url = reverse('bdr.backend:dataset-files', kwargs={'ds': self.DATASET.slug})
        response = self.client.get(url)
        self.assertJSONEqual(response.content, {'files': [{'name': name, 'href': file_obj.get_absolute_url(),
                                                           'default_format': self.FORMAT.get_absolute_url(),
                                                           'revisions': 0, 'tags': []}]})

    def test_includes_revision_count(self):
        """Check that file references includes an accurate revision count."""
        from random import randint
        name = 'example.txt'
        file_obj = models.File.objects.create(name=name, default_format=self.FORMAT, dataset=self.DATASET)
        revision_count = randint(1, 10)
        for i in range(1, revision_count + 1):
            models.Revision.objects.create(level=i, file=file_obj, size=0, format=self.FORMAT,
                                           updated_at=datetime.now(utc))

        url = reverse('bdr.backend:dataset-files', kwargs={'ds': self.DATASET.slug})
        response = self.client.get(url)
        self.assertJSONEqual(response.content, {'files': [{'name': name, 'href': file_obj.get_absolute_url(),
                                                           'default_format': self.FORMAT.get_absolute_url(),
                                                           'revisions': revision_count, 'tags': []}]})

    def test_includes_tag_reference(self):
        """Check that tag references match the API format."""
        name = 'example.txt'
        file_obj = models.File.objects.create(name=name, default_format=self.FORMAT, dataset=self.DATASET)
        tag = models.Tag.objects.create(name='Example')
        file_obj.tags.add(tag)

        response = self.client.get(reverse('bdr.backend:dataset-files', kwargs={'ds': self.DATASET.slug}))
        self.assertJSONEqual(response.content, {'files': [{'name': name, 'href': file_obj.get_absolute_url(),
                                                           'revisions': 0,
                                                           'default_format': self.FORMAT.get_absolute_url(),
                                                           'tags': [{'name': tag.name,
                                                                     'href': tag.get_absolute_url()}]}]})


class RevisionDetailViewTest(TestCase):
    def setUp(self):
        self.ENCODER = DjangoJSONEncoder()
        self.DATASET = models.Dataset.objects.create(name='Test', slug='test')
        self.FORMAT = models.Format.objects.get(slug='raw')
        self.FILE = models.File.objects.create(name='example.txt', dataset=self.DATASET, default_format=self.FORMAT)
        self.REVISION = models.Revision.objects.create(file=self.FILE, level=1, size=0, format=self.FORMAT,
                                                       updated_at=datetime.now(utc))
        self.TAG = models.Tag.objects.create(name='testing')

    def test_non_existent_dataset_returns_404(self):
        """Ensure that a 404 HTTP response code is returned if no dataset matches a given identifier."""
        response = self.client.head(reverse('bdr.backend:revision-detail', kwargs={'ds': 'missing', 'fn': 'missing',
                                                                                   'rev': 0}))
        self.assertEqual(404, response.status_code)

    def test_non_existent_file_returns_404(self):
        """Ensure that a 404 HTTP response code is returned if no file matches a given identifier."""
        response = self.client.head(reverse('bdr.backend:revision-detail', kwargs={'ds': self.DATASET.slug,
                                                                                   'fn': 'missing',
                                                                                   'rev': 0}))
        self.assertEqual(404, response.status_code)

    def test_non_existent_revision_returns_404(self):
        """Ensure that a 404 HTTP response code is returned if no revision matches a given identifier."""
        response = self.client.head(reverse('bdr.backend:revision-detail', kwargs={'ds': self.DATASET.slug,
                                                                                   'fn': self.FILE.name,
                                                                                   'rev': 0}))
        self.assertEqual(404, response.status_code)

    def test_head_returns_200(self):
        """Ensure that a request for a matched identifier returns a 200 HTTP response code."""
        response = self.client.head(reverse('bdr.backend:revision-detail', kwargs={'ds': self.DATASET.slug,
                                                                                   'fn': self.FILE.name,
                                                                                   'rev': self.REVISION.level}))
        self.assertEqual(200, response.status_code)

    def test_get_returns_basic_data(self):
        """Check that, with a valid identifier, basic fields are populated and match the API format."""
        level = self.REVISION.level
        url = reverse('bdr.backend:revision-detail', kwargs={'ds': self.DATASET.slug, 'fn': self.FILE.name,
                                                             'rev': level})
        response = self.client.get(url)
        self.assertJSONEqual(response.content,
                             {'revision': level, 'href': url, 'size': self.REVISION.size,
                              'format': self.FORMAT.get_absolute_url(),
                              'updated_at': self.ENCODER.default(self.REVISION.updated_at), 'tags': []})

    def test_get_includes_tag_reference(self):
        """Check that tag references match the API format."""
        self.REVISION.tags.add(self.TAG)

        level = self.REVISION.level
        url = reverse('bdr.backend:revision-detail', kwargs={'ds': self.DATASET.slug, 'fn': self.FILE.name,
                                                             'rev': level})
        response = self.client.get(url)
        self.assertJSONEqual(response.content,
                             {'revision': level, 'href': url, 'size': self.REVISION.size,
                              'format': self.FORMAT.get_absolute_url(),
                              'updated_at': self.ENCODER.default(self.REVISION.updated_at),
                              'tags': [{'name': self.TAG.name, 'href': self.TAG.get_absolute_url()}]})


class RevisionCollectionViewTest(TestCase):
    def setUp(self):
        self.ENCODER = DjangoJSONEncoder()
        self.DATASET = models.Dataset.objects.create(name='Test', slug='test')
        self.FORMAT = models.Format.objects.get(slug='raw')
        self.FILE = models.File.objects.create(name='example.txt', dataset=self.DATASET, default_format=self.FORMAT)

    def test_collection_returns_200(self):
        """Ensure that this collection view always succeeds, even if there are no revisions for a file."""
        response = self.client.get(reverse('bdr.backend:file-revisions', kwargs={'ds': self.DATASET.slug,
                                                                                 'fn': self.FILE.name}))
        self.assertEquals(200, response.status_code)

    def test_no_revisions_returns_empty_list(self):
        """Check that the revision collection is an empty list when no revisions have been added."""
        response = self.client.get(reverse('bdr.backend:file-revisions', kwargs={'ds': self.DATASET.slug,
                                                                                 'fn': self.FILE.name}))
        self.assertJSONEqual(response.content, {'revisions': []})

    def test_returns_revision_reference(self):
        """Check that r references match the API format."""
        level, size = 1, 0
        revision = models.Revision.objects.create(level=level, format=self.FORMAT, file=self.FILE, size=size,
                                                  updated_at=datetime.now(utc))

        response = self.client.get(reverse('bdr.backend:file-revisions', kwargs={'ds': self.DATASET.slug,
                                                                                 'fn': self.FILE.name}))
        self.assertJSONEqual(response.content, {'revisions': [{'revision': level, 'href': revision.get_absolute_url(),
                                                               'format': self.FORMAT.get_absolute_url(), 'size': size,
                                                               'updated_at': self.ENCODER.default(revision.updated_at),
                                                               'tags': []}]})

    def test_includes_tag_reference(self):
        """Check that tag references match the API format."""
        level, size = 1, 0
        revision = models.Revision.objects.create(level=level, format=self.FORMAT, file=self.FILE, size=size,
                                                  updated_at=datetime.now(utc))
        tag = models.Tag.objects.create(name='example')
        revision.tags.add(tag)

        response = self.client.get(reverse('bdr.backend:file-revisions', kwargs={'ds': self.DATASET.slug,
                                                                                 'fn': self.FILE.name}))
        self.assertJSONEqual(response.content, {'revisions': [{'revision': level, 'href': revision.get_absolute_url(),
                                                               'format': self.FORMAT.get_absolute_url(), 'size': size,
                                                               'updated_at': self.ENCODER.default(revision.updated_at),
                                                               'tags': [{'name': tag.name,
                                                                         'href': tag.get_absolute_url()}]}]})
