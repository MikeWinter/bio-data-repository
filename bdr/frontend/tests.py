"""
The test suite for the Biological Dataset Repository front-end web application.
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

from datetime import datetime
from random import randrange
import io
import urlparse

from django.core import management
from django.test import LiveServerTestCase
from django.db.transaction import atomic
from django.core.urlresolvers import reverse

from . import app_settings
from . import models as frontend
from ..backend import models as backend
from ..utils import utc


class ServerTestMixin(object):
    def setUp(self):
        components = urlparse.urlsplit(self.live_server_url)
        base = urlparse.urlunsplit((components.scheme, '127.0.0.1:%i' % components.port, '', '', ''))
        app_settings.STORAGE_URL = urlparse.urljoin(base, urlparse.urlsplit(app_settings.STORAGE_URL).path)
        with io.BytesIO() as f:
            management.call_command('clearapicache', stdout=f)

    def tearDown(self):
        with io.BytesIO() as f:
            management.call_command('clearapicache', stdout=f)


class HomePageViewTest(ServerTestMixin, LiveServerTestCase):
    def test_http_ok(self):
        """Check that the URL route is configured correctly and a 200 response code is received."""
        with atomic():
            response = self.client.get(reverse('bdr.frontend:home'))
        self.assertEqual(200, response.status_code)

    def test_empty(self):
        """
        Ensure that a user is presented with an informative message, rather than an empty page, if there are no
        datasets.
        """
        with atomic():
            response = self.client.get(reverse('bdr.frontend:home'))
        self.assertContains(response, 'No datasets have been added')

    def test_lists_datasets(self):
        """Ensure that an uncatalogued dataset can be displayed in the menu."""
        title = 'DrugBank'
        with atomic():
            dataset = backend.Dataset.objects.create(name=title, slug='drugbank')
            response = self.client.get(reverse('bdr.frontend:home'))
            local = frontend.Dataset.objects.get(href=dataset.get_absolute_url())
        expected = '<a href="{url}">{title}</a>'.format(title=title, url=local.get_absolute_url())
        self.assertInHTML(expected, response.content)

    def test_lists_category(self):
        """Ensure that categories are listed in the menu."""
        title = 'Genomics'
        slug = 'genomics'
        with atomic():
            category = backend.Category.objects.create(name=title, slug=slug)
            response = self.client.get(reverse('bdr.frontend:home'))
        expected = '''
        <a data-toggle="collapse" data-parent="#group-{slug}" href="#child-{slug}" aria-controls="child-{slug}">
            {title} <span class="caret"></span>
        </a>
        '''.format(title=title, slug=slug)
        self.assertInHTML(expected, response.content)

    def test_lists_categorised_dataset(self):
        """Examine output for the correct grouping of datasets and their parent categories."""
        category_title = 'Genomics'
        category_slug = 'genomics'
        dataset_title = 'HPRD'
        dataset_slug = 'hprd'
        with atomic():
            category = backend.Category.objects.create(name=category_title, slug=category_slug)
            dataset = backend.Dataset.objects.create(name=dataset_title, slug=dataset_slug)
            dataset.categories.add(category)
            response = self.client.get(reverse('bdr.frontend:home'))
            local = frontend.Dataset.objects.get(href=dataset.get_absolute_url())
        expected = '''
        <li id="group-{category_slug}" class="panel panel-default" role="tablist" aria-multiselectable="true">
            <div id="tab-{category_slug}" class="panel-heading" role="tab">
                <div class="panel-title">
                    <a data-toggle="collapse" data-parent="#group-{category_slug}" href="#child-{category_slug}"
                       aria-controls="child-{category_slug}">{category} <span class="caret"></span></a>
                </div>
            </div>
            <div id="child-{category_slug}" class="panel-collapse collapse" role="tabpanel"
                 aria-labelledby="group-{category_slug}">
                <ul class="list-group">
                    <li class="list-group-item"><a href="{url}">{dataset}</a></li>
                </ul>
            </div>
        </li>'''.format(category=category_title, category_slug=category_slug, dataset=dataset_title,
                        url=local.get_absolute_url())
        self.assertInHTML(expected, response.content)

        # Subcategories have been disabled.
        # def test_lists_subcategory(self):
        # """Examine output for the correct grouping of subcategories with their parents."""
        #     category_title = 'Genomics'
        #     category_slug = 'genomics'
        #     subcategory_title = 'Human'
        #     subcategory_slug = 'human'
        #     with atomic():
        #         category = backend.Category.objects.create(name=category_title, slug=category_slug)
        #         backend.Category.objects.create(name=subcategory_title, slug=subcategory_slug, parent=category)
        #         response = self.client.get(reverse('bdr.frontend:home'))
        #     expected = '''
        #     <li id="group-{parent_slug}" class="panel panel-default" role="tablist" aria-multiselectable="true">
        #         <div id="tab-{parent_slug}" class="panel-heading" role="tab">
        #             <div class="panel-title">
        #                 <a data-toggle="collapse" data-parent="#group-{parent_slug}" href="#child-{parent_slug}" aria-controls="child-{parent_slug}">{parent} <span class="caret"></span></a>
        #             </div>
        #         </div>
        #         <div id="child-{parent_slug}" class="panel-collapse collapse" role="tabpanel" aria-labelledby="group-{parent_slug}">
        #             <div class="panel-body" style="padding: 0.5em 0.5em 0.5em 1em">
        #             <ul class="panel-group list-unstyled" style="margin-bottom: 0">
        #                 <li id="group-{child_slug}" class="panel panel-default" role="tablist" aria-multiselectable="true">
        #                 <div id="tab-{child_slug}" class="panel-heading" role="tab">
        #                     <div class="panel-title">
        #                         <a data-toggle="collapse" data-parent="#group-{child_slug}" href="#child-{child_slug}" aria-controls="child-{child_slug}">{child} <span class="caret"></span></a>
        #                     </div>
        #                 </div>
        #                 <div id="child-{child_slug}" class="panel-collapse collapse" role="tabpanel" aria-labelledby="group-{child_slug}">
        #                     Empty
        #                 </div>
        #                 </li>
        #             </ul>
        #             </div>
        #             Empty
        #         </div>
        #     </li>'''.format(parent=category_title, parent_slug=category_slug, child=subcategory_title,
        #                     child_slug=subcategory_slug)
        #     self.assertInHTML(expected, response.content)


class DatasetListViewTest(ServerTestMixin, LiveServerTestCase):
    def test_http_ok(self):
        """Check that the URL route is configured correctly and a 200 response code is received."""
        response = self.client.get(reverse('bdr.frontend:datasets'))
        self.assertEqual(200, response.status_code)

    def test_empty(self):
        """
        Ensure that a user is presented with an informative message, rather than an empty page, if there are no
        datasets.
        """
        response = self.client.get(reverse('bdr.frontend:datasets'))
        self.assertContains(response, 'No datasets have been added')

    def test_lists_datasets(self):
        """Check that datasets are listed in the response."""
        title = 'DrugBank'
        dataset = backend.Dataset.objects.create(name=title, slug='drugbank')
        response = self.client.get(reverse('bdr.frontend:datasets'))
        local = frontend.Dataset.objects.get(href=dataset.get_absolute_url())
        expected = '<th colspan="2"><a href="{uri}">{title}</a></th>'.format(
            uri=local.get_absolute_url(), title=title)
        self.assertInHTML(expected, response.content)

    def test_datasets_include_file_count(self):
        """Verify that the number of files displayed is correct."""
        from random import randrange
        title = 'DrugBank'
        dataset = backend.Dataset.objects.create(name=title, slug='drugbank')
        format = backend.Format.objects.get(slug='raw')
        file_count = randrange(100)
        for i in range(file_count):
            backend.File.objects.create(dataset=dataset, name=str(i), default_format=format)
        response = self.client.get(reverse('bdr.frontend:datasets'))
        local = frontend.Dataset.objects.get(href=dataset.get_absolute_url())
        expected = '''
        <tr>
            <th colspan="2"><a href="{uri}">{title}</a></th>
            <td>{count}</td>
        </tr>'''.format(uri=local.get_absolute_url(), title=title, count=file_count)
        self.assertInHTML(expected, response.content)

    def test_list_no_category(self):
        """Ensures that the datasets listing correctly handles datasets with no categorisation."""
        dataset_title = 'DrugBank'
        dataset = backend.Dataset.objects.create(name=dataset_title, slug='drugbank')

        response = self.client.get(reverse('bdr.frontend:datasets'))
        local = frontend.Dataset.objects.get(href=dataset.get_absolute_url())
        expected = '''
        <tbody>
        <tr>
            <th colspan="2"><a href="{uri}">{dataset}</a></th>
            <td>0</td>
        </tr>
        <tr>
            <th>Categories:</th>
            <td>None</td>
            <td class="text-right" colspan="2"></td>
        </tr>
        </tbody>
        '''.format(uri=local.get_absolute_url(), dataset=dataset_title)
        self.assertInHTML(expected, response.content)

    def test_lists_categories(self):
        """Check that the categories of datasets are listed in the response."""
        category1_title, category1_slug, category2_title, category2_slug = 'Gene Ontology', 'go', 'Human', 'human'
        category1 = backend.Category.objects.create(name=category1_title, slug=category1_slug)
        category2 = backend.Category.objects.create(name=category2_title, slug=category2_slug)

        dataset_title = 'UniProt GOA'
        dataset = backend.Dataset.objects.create(name=dataset_title, slug='goa')
        dataset.categories.add(category1)
        dataset.categories.add(category2)

        response = self.client.get(reverse('bdr.frontend:datasets'))
        local = frontend.Dataset.objects.get(href=dataset.get_absolute_url())
        expected = '''
        <tbody>
        <tr>
            <th colspan="2"><a href="{uri}">{dataset}</a></th>
            <td>0</td>
        </tr>
        <tr>
            <th>Categories:</th>
            <td>{category1} {category2}</td>
            <td class="text-right" colspan="2"></td>
        </tr>
        </tbody>
        '''.format(uri=local.get_absolute_url(), dataset=dataset_title, category1=category1_title,
                   category2=category2_title)
        self.assertInHTML(expected, response.content)

    def test_lists_tags(self):
        """Check that the tags of datasets are listed in the response."""
        tag_title = 'test'
        tag = backend.Tag.objects.create(name=tag_title)

        dataset_title = 'DrugBank'
        dataset = backend.Dataset.objects.create(name=dataset_title, slug='drugbank')
        dataset.tags.add(tag)

        response = self.client.get(reverse('bdr.frontend:datasets'))
        local = frontend.Dataset.objects.get(href=dataset.get_absolute_url())
        expected = '''
        <tbody>
        <tr>
            <th colspan="2"><a href="{dataset_uri}">{dataset}</a></th>
            <td>0</td>
        </tr>
        <tr>
            <th>Categories:</th>
            <td>None</td>
            <td class="text-right" colspan="2">
                <a class="label label-default" href="/explorer/search?query=%23{tag}">#{tag}</a>
            </td>
        </tr>
        </tbody>
        '''.format(dataset=dataset_title, dataset_uri=local.get_absolute_url(), tag=tag_title)
        self.assertInHTML(expected, response.content)


class DatasetDetailViewTest(ServerTestMixin, LiveServerTestCase):
    def test_http_ok(self):
        """
        Check that the URL route is configured correctly and a 200 response code is received.

        This test also requires that dataset lookup proceeds correctly as a valid slug is required as part of the route.
        """
        slug = 'drugbank'
        with atomic():
            backend.Dataset.objects.create(name='DrugBank', slug=slug)
            response = self.client.get(reverse('bdr.frontend:dataset-detail', kwargs={'slug': slug}))
        self.assertEqual(200, response.status_code)

    def test_http_not_found(self):
        """Check that a non-existent dataset keyword results in a Not Found response."""
        with atomic():
            response = self.client.get(reverse('bdr.frontend:dataset-detail', kwargs={'slug': 'does-not-exist'}))
        self.assertEqual(404, response.status_code)

    def test_shows_title(self):
        """Check that the correct dataset is named in the response."""
        title, slug = 'DrugBank', 'drugbank'
        with atomic():
            backend.Dataset.objects.create(name=title, slug=slug)
            response = self.client.get(reverse('bdr.frontend:dataset-detail', kwargs={'slug': slug}))
        expected = '<h1>{title}</h1>'.format(title=title)
        self.assertInHTML(expected, response.content)

    def test_lists_tags(self):
        """Check that the tags for the dataset are included."""
        tag_title = 'test'
        dataset_title, slug = 'DrugBank', 'drugbank'
        with atomic():
            tag = backend.Tag.objects.create(name=tag_title)
            dataset = backend.Dataset.objects.create(name=dataset_title, slug=slug)
            dataset.tags.add(tag)

            response = self.client.get(reverse('bdr.frontend:dataset-detail', kwargs={'slug': slug}))
        expected = '''
        <h1>
            {dataset}
            <a class="label label-default tag" href="/explorer/search?query=%23{tag}">#{tag}</a>
        </h1>
        '''.format(dataset=dataset_title, tag=tag_title)
        self.assertInHTML(expected, response.content)

    def test_lists_categories(self):
        """Check that the categories of datasets are listed in the response."""
        category_title = 'Gene Ontology'
        category_slug = 'go'
        dataset_slug = 'goa'
        with atomic():
            category = backend.Category.objects.create(name=category_title, slug=category_slug)
            dataset = backend.Dataset.objects.create(name='UniProt GOA', slug=dataset_slug)
            dataset.categories.add(category)

            response = self.client.get(reverse('bdr.frontend:dataset-detail', kwargs={'slug': dataset_slug}))
            local = frontend.Category.objects.get(slug=category_slug)
        expected = '''
        <ol class="breadcrumb">
            <li><a href="{url}">{category}</a></li>
        </ol>
        '''.format(category=category_title, url=local.get_absolute_url())
        self.assertInHTML(expected, response.content)

    def test_display_notes(self):
        slug, note = 'drugbank', 'This is a test!'
        with atomic():
            backend.Dataset.objects.create(name='DrugBank', slug=slug, notes=note)
            response = self.client.get(reverse('bdr.frontend:dataset-detail', kwargs={'slug': slug}))
        expected = '<p>{note}</p>'.format(note=note)
        self.assertInHTML(expected, response.content)

    def test_no_files(self):
        """
        Ensure that a user is presented with an informative message, rather than an empty list, if there are no files in
        a dataset.
        """
        slug = 'drugbank'
        with atomic():
            backend.Dataset.objects.create(name='DrugBank', slug=slug)
            response = self.client.get(reverse('bdr.frontend:dataset-detail', kwargs={'slug': slug}))
        self.assertInHTML('<p class="alert alert-warning">There are no files in this dataset.</p>', response.content)

    def test_lists_files(self):
        """Check that a correct list of files, including their links, are displayed in the response."""
        slug = 'drugbank'
        filename = 'drugbank.xml'
        with atomic():
            dataset = backend.Dataset.objects.create(name='DrugBank', slug=slug)
            format = backend.Format.objects.get(slug='raw')
            file = backend.File.objects.create(name=filename, dataset=dataset, default_format=format)

            response = self.client.get(reverse('bdr.frontend:dataset-detail', kwargs={'slug': slug}))
            local = frontend.File.objects.get(href=file.get_absolute_url())
        expected = '<th><a href="{uri}">{name}</a>'.format(
            name=filename, uri=local.get_absolute_url())
        self.assertInHTML(expected, response.content)

    def test_includes_latest_revision_link(self):
        """Check that the link to the file is for the latest revision of that file."""
        slug = 'drugbank'
        filename = 'drugbank.xml'
        with atomic():
            dataset = backend.Dataset.objects.create(name='DrugBank', slug=slug)
            format = backend.Format.objects.get(slug='raw')
            file = backend.File.objects.create(name=filename, dataset=dataset, default_format=format)
            now = datetime.now(utc)

            revision_count = randrange(100)
            for i in range(revision_count):
                backend.Revision.objects.create(file=file, level=i + 1, size=0, format=format, updated_at=now)

            response = self.client.get(reverse('bdr.frontend:dataset-detail', kwargs={'slug': slug}))
            local = frontend.File.objects.get(href=file.get_absolute_url())
        expected = '''
        <a class="btn btn-link btn-xs" href="{path}latest"
           title="Download latest revision">
            <span class="glyphicon glyphicon-download" aria-hidden="true"></span>
        </a>
        '''.format(path=local.get_absolute_url())
        self.assertInHTML(expected, response.content)

    def test_lists_revision_count(self):
        """
        Ensure that the number of stated revisions is correct.

        While the previous test generally ensures that this will be the case (as the latest revision number will
        normally be equal to the number of revisions), if an intermediate revision is removed this will no longer be so.
        """
        slug = 'drugbank'
        filename = 'drugbank.xml'
        with atomic():
            dataset = backend.Dataset.objects.create(name='DrugBank', slug=slug)
            format = backend.Format.objects.get(slug='raw')
            file = backend.File.objects.create(name=filename, dataset=dataset, default_format=format)
            now = datetime.now(utc)

            # Generate a list of revision numbers that may be sparse (and therefore include fewer total elements than
            # implied by the last such revision number.
            revisions = list(range(1, randrange(100), randrange(2) + 1))
            for i in revisions:
                backend.Revision.objects.create(file=file, level=i, size=0, format=format, updated_at=now)
            response = self.client.get(reverse('bdr.frontend:dataset-detail', kwargs={'slug': slug}))
            local = frontend.File.objects.get(href=file.get_absolute_url())

        expected = '''
        <tr>
            <th>
                <a href="{path}">{name}</a>
                <a class="btn btn-link btn-xs" href="{path}latest"
                   title="Download latest revision">
                    <span class="glyphicon glyphicon-download" aria-hidden="true"></span>
                </a>
            </th>
            <td>{revisions}</td>
            <td class="text-right"></td>
        </tr>
        '''.format(path=local.get_absolute_url(), name=filename, revisions=len(revisions))
        self.assertInHTML(expected, response.content)
