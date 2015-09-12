from django.core.urlresolvers import reverse
from django.test import TransactionTestCase

from ..models import Dataset, File, Category, Tag
from .test_models import _get_random_text

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


# TODO: Add ordering tests for categories and updates, and exclusion tests for categories with no
# TODO: associated datasets.
class HomePageViewTest(TransactionTestCase):
    def test_http_ok(self):
        """Check that the URL route is configured correctly and a 200 response code is received."""
        response = self.client.get(reverse('bdr:home'))

        self.assertEqual(200, response.status_code)

    def test_empty(self):
        """
        Ensure that a user is presented with an informative message, rather than an empty page, if there are no
        datasets.
        """
        response = self.client.get(reverse('bdr:home'))

        self.assertContains(response, 'No datasets have been added')

    def test_lists_datasets(self):
        """Ensure that an uncatalogued dataset can be displayed in the menu."""
        name = _get_random_text()
        dataset = Dataset.objects.create(name=name)
        expected = '<a href="{url}">{title}</a>'.format(title=name, url=dataset.get_absolute_url())

        response = self.client.get(reverse('bdr:home'))

        self.assertInHTML(expected, response.content)

    # Will not pass as this expects an unused category to be listed: it won't.
    # def test_lists_category(self):
    #     """Ensure that categories are listed in the menu."""
    #     name = _get_random_text()
    #     category = Category.objects.create(name=name)
    #     category_id = category.id
    #     # TODO: Replace with category.get_absolute_url() once implemented
    #     category_url = "/"
    #     response = self.client.get(reverse('bdr:home'))
    #     expected = '''
    #     <a data-toggle="collapse" data-target="#child-{id}" href="{url}" aria-controls="child-{id}"
    #        aria-expanded="false">
    #         {title} <span class="caret"></span>
    #     </a>
    #     '''.format(title=name, id=category_id, url=category_url)
    #     print response.content
    #     self.assertInHTML(expected, response.content)

    def test_lists_categorised_dataset(self):
        """Examine output for the correct grouping of datasets and their parent categories."""
        category_name = _get_random_text()
        dataset_name = _get_random_text()
        category = Category.objects.create(name=category_name)
        category_id = category.id
        category_url = category.get_absolute_url()
        dataset = Dataset.objects.create(name=dataset_name)
        dataset_url = dataset.get_absolute_url()
        dataset.categories.add(category)
        response = self.client.get(reverse('bdr:home'))
        expected = '''
        <li id="group-{category_id}" class="panel panel-default">
            <div id="tab-{category_id}" class="panel-heading" role="tab">
                <div class="panel-title">
                    <a href="{category_url}" data-toggle="collapse"
                       data-target="#child-{category_id}" aria-controls="child-{category_id}"
                       aria-expanded="false">{category} <span class="caret"></span></a>
                </div>
            </div>
            <div id="child-{category_id}" class="panel-collapse collapse" role="tabpanel"
                 aria-labelledby="group-{category_id}">
                <ul class="list-group">
                    <li class="list-group-item"><a href="{dataset_url}">{dataset}</a></li>
                </ul>
            </div>
        </li>'''.format(category=category_name, category_id=category_id, category_url=category_url,
                        dataset=dataset_name, dataset_url=dataset_url)
        self.assertInHTML(expected, response.content)


class DatasetListViewTest(TransactionTestCase):
    def test_http_ok(self):
        """Check that the URL route is configured correctly and a 200 response code is received."""
        response = self.client.get(reverse('bdr:datasets'))

        self.assertEqual(200, response.status_code)

    def test_empty(self):
        """
        Ensure that a user is presented with an informative message, rather than an empty page, if there are no
        datasets.
        """
        response = self.client.get(reverse('bdr:datasets'))

        self.assertContains(response, 'No datasets have been added')

    def test_lists_datasets(self):
        """Check that datasets are listed in the response."""
        title = 'DrugBank'
        dataset = Dataset.objects.create(name=title)
        expected = '<th><a href="{uri}">{title}</a></th>'.format(
            uri=dataset.get_absolute_url(), title=title)

        response = self.client.get(reverse('bdr:datasets'))

        self.assertInHTML(expected, response.content)

    def test_datasets_include_file_count(self):
        """Verify that the number of files displayed is correct."""
        from random import randrange
        title = 'DrugBank'
        dataset = Dataset.objects.create(name=title)
        file_count = randrange(100)
        for i in range(file_count):
            File.objects.create(dataset=dataset, name=str(i))
        expected = '''
        <tr>
            <th><a href="{uri}">{title}</a></th>
            <td>{count}</td>
        </tr>'''.format(uri=dataset.get_absolute_url(), title=title, count=file_count)

        response = self.client.get(reverse('bdr:datasets'))

        self.assertInHTML(expected, response.content)

    def test_list_no_category(self):
        """Ensures that the datasets listing correctly handles datasets with no categorisation."""
        dataset_title = 'DrugBank'
        dataset = Dataset.objects.create(name=dataset_title)
        expected = '''
        <tbody>
        <tr>
            <th><a href="{uri}">{dataset}</a></th>
            <td>0</td>
        </tr>
        <tr class="small">
            <td>
                <span class="pull-left">Categories:&nbsp;</span>
                <ul class="list-inline">
                    <li>None</li>
                </ul>
            </td>
            <td class="text-right"></td>
        </tr>
        </tbody>
        '''.format(uri=dataset.get_absolute_url(), dataset=dataset_title)

        response = self.client.get(reverse('bdr:datasets'))

        self.assertInHTML(expected, response.content)

    def test_lists_categories(self):
        """Check that the categories of datasets are listed in the response."""
        category1_title, category2_title = 'Gene Ontology', 'Human'
        category1 = Category.objects.create(name=category1_title)
        category2 = Category.objects.create(name=category2_title)
        category1_url = category1.get_absolute_url()
        category2_url = category2.get_absolute_url()

        dataset_title = 'UniProt GOA'
        dataset = Dataset.objects.create(name=dataset_title)
        dataset.categories.add(category1)
        dataset.categories.add(category2)

        expected = '''
        <tbody>
        <tr>
            <th><a href="{uri}">{dataset}</a></th>
            <td>0</td>
        </tr>
        <tr class="small">
            <td>
                <span class="pull-left">Categories:&nbsp;</span>
                <ul class="list-inline">
                    <li><a href="{category1_url}">{category1}</a></li>
                    <li><a href="{category2_url}">{category2}</a></li>
                </ul>
            </td>
            <td class="text-right"></td>
        </tr>
        </tbody>
        '''.format(uri=dataset.get_absolute_url(), dataset=dataset_title, category1=category1_title,
                   category1_url=category1_url, category2=category2_title,
                   category2_url=category2_url)

        response = self.client.get(reverse('bdr:datasets'))

        self.assertInHTML(expected, response.content)

    def test_lists_tags(self):
        """Check that the tags of datasets are listed in the response."""
        tag_title = 'test'
        tag = Tag.objects.create(name=tag_title)

        dataset_title = 'DrugBank'
        dataset = Dataset.objects.create(name=dataset_title)
        dataset.tags.add(tag)

        expected = '''
        <tbody>
        <tr>
            <th><a href="{dataset_uri}">{dataset}</a></th>
            <td>0</td>
        </tr>
        <tr class="small">
            <td>
                <span class="pull-left">Categories:&nbsp;</span>
                <ul class="list-inline">
                    <li>None</li>
                </ul>
            </td>
            <td class="text-right">
                <ul class="list-inline">
                    <li><a class="label label-default"
                           href="/explorer/tags/{tag}">#{tag}</a></li>
                </ul>
            </td>
        </tr>
        </tbody>
        '''.format(dataset=dataset_title, dataset_uri=dataset.get_absolute_url(), tag=tag_title)

        response = self.client.get(reverse('bdr:datasets'))

        self.assertInHTML(expected, response.content)


class DatasetDetailViewTest(TransactionTestCase):
    def test_http_ok(self):
        """
        Check that the URL route is configured correctly and a 200 response code is received.

        This test also requires that dataset lookup proceeds correctly as a valid slug is required as part of the route.
        """
        dataset = Dataset.objects.create(name='DrugBank')

        response = self.client.get(reverse('bdr:dataset', kwargs={'pk': dataset.pk,
                                                                  'name': dataset.name}))

        self.assertEqual(200, response.status_code)

    def test_http_not_found(self):
        """Check that a non-existent dataset keyword results in a Not Found response."""
        response = self.client.get(reverse('bdr:dataset', kwargs={'pk': 0,
                                                                  'name': 'does-not-exist'}))

        self.assertEqual(404, response.status_code)

    def test_shows_title(self):
        """Check that the correct dataset is named in the response."""
        title = 'DrugBank'
        dataset = Dataset.objects.create(name=title)
        expected = '<h1>{title}</h1>'.format(title=title)

        response = self.client.get(reverse('bdr:dataset', kwargs={'pk': dataset.pk,
                                                                  'name': title}))

        self.assertInHTML(expected, response.content)

    def test_lists_tags(self):
        """Check that the tags for the dataset are included."""
        tag_title = 'test'
        dataset_title = 'DrugBank'
        tag = Tag.objects.create(name=tag_title)
        dataset = Dataset.objects.create(name=dataset_title)
        dataset.tags.add(tag)
        expected = '''
        <h1>
            {dataset}
            <a class="label label-default tag" href="/explorer/search?query={tag}">#{tag}</a>
        </h1>
        '''.format(dataset=dataset_title, tag=tag_title)

        response = self.client.get(reverse('bdr:dataset', kwargs={'pk': dataset.pk,
                                                                  'name': dataset_title}))

        self.assertInHTML(expected, response.content)

    def test_lists_categories(self):
        """Check that the categories of datasets are listed in the response."""
        category_title = 'Gene Ontology'
        category = Category.objects.create(name=category_title)
        dataset = Dataset.objects.create(name='UniProt')
        dataset.categories.add(category)
        expected = '''
        <tr>
            <th>Categories</th>
            <td>
                <ul class="list-inline">
                    <li><a href="{url}">{category}</a></li>
                </ul>
            </td>
        </tr>
        '''.format(category=category_title, url=category.get_absolute_url())

        response = self.client.get(reverse('bdr:dataset', kwargs={'pk': dataset.pk,
                                                                  'name': dataset.name}))

        self.assertInHTML(expected, response.content)

    def test_display_notes(self):
        note = 'This is a test!'
        dataset = Dataset.objects.create(name='DrugBank', notes=note)
        expected = '''
        <tr>
            <th>Notes</th>
            <td>{note}</td>
        </tr>
        '''.format(note=note)

        response = self.client.get(reverse('bdr:dataset', kwargs={'pk': dataset.pk,
                                                                  'name': dataset.name}))

        self.assertInHTML(expected, response.content)

    def test_no_files(self):
        """
        Ensure that a user is presented with an informative message, rather than an empty list, if there are no files in
        a dataset.
        """
        dataset = Dataset.objects.create(name='DrugBank')

        response = self.client.get(reverse('bdr:dataset', kwargs={'pk': dataset.pk,
                                                                  'name': dataset.name}))

        self.assertInHTML('<p>There are no files in this dataset.</p>', response.content)

    def test_lists_files(self):
        """Check that a correct list of files, including their links, are displayed in the response."""
        filename = 'drugbank.xml'
        dataset = Dataset.objects.create(name='DrugBank')
        expected = '<th><a href="">{name}</a>'.format(name=filename)

        File.objects.create(name=filename, dataset=dataset)
        response = self.client.get(reverse('bdr:dataset', kwargs={'pk': dataset.pk,
                                                                  'name': dataset.name}))

        self.assertInHTML(expected, response.content)

    # def test_includes_latest_revision_link(self):
    #     """Check that the link to the file is for the latest revision of that file."""
    #     slug = 'drugbank'
    #     filename = 'drugbank.xml'
    #     with atomic():
    #         dataset = backend.Dataset.objects.create(name='DrugBank', slug=slug)
    #         format = backend.Format.objects.get(slug='raw')
    #         file = backend.File.objects.create(name=filename, dataset=dataset, default_format=format)
    #         now = datetime.now(utc)
    #
    #         revision_count = randrange(100)
    #         for i in range(revision_count):
    #             backend.Revision.objects.create(file=file, level=i + 1, size=0, format=format, updated_at=now)
    #
    #         response = self.client.get(reverse('bdr.frontend:dataset-detail', kwargs={'slug': slug}))
    #         local = frontend.File.objects.get(href=file.get_absolute_url())
    #     expected = '''
    #     <a class="btn btn-link btn-xs" href="{path}latest"
    #        title="Download latest revision">
    #         <span class="glyphicon glyphicon-download" aria-hidden="true"></span>
    #     </a>
    #     '''.format(path=local.get_absolute_url())
    #     self.assertInHTML(expected, response.content)

    # def test_lists_revision_count(self):
    #     """
    #     Ensure that the number of stated revisions is correct.
    #
    #     While the previous test generally ensures that this will be the case (as the latest revision number will
    #     normally be equal to the number of revisions), if an intermediate revision is removed this will no longer be so.
    #     """
    #     filename = 'drugbank.xml'
    #     dataset = Dataset.objects.create(name='DrugBank')
    #     file = File.objects.create(name=filename, dataset=dataset)
    #
    #     # Generate a list of revision numbers that may be sparse (and therefore include fewer total elements than
    #     # implied by the last such revision number.
    #     revisions = list(range(1, randrange(100), randrange(2) + 1))
    #     for i in revisions:
    #         update = Update
    #         Revision.objects.create(file=file, number=i, size=0)
    #     expected = '''
    #     <tr>
    #         <th>
    #             <a href="">{name}</a>
    #             <a class="btn btn-link btn-xs" href=""
    #                title="Download latest revision">
    #                 <span class="glyphicon glyphicon-download" aria-hidden="true"></span>
    #             </a>
    #         </th>
    #         <td>{revisions}</td>
    #         <td class="text-right"></td>
    #     </tr>
    #     '''.format(name=filename, revisions=len(revisions))
    #
    #     response = self.client.get(reverse('bdr:dataset', kwargs={'pk': dataset.pk,
    #                                                               'name': dataset.name}))
    #
    #     self.assertInHTML(expected, response.content)