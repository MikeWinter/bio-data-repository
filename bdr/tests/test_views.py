from django.core.urlresolvers import reverse
from django.db.transaction import atomic
from django.test import LiveServerTestCase

from frontend.tests import ServerTestMixin
from bdr.models import Category, Dataset
from .test_models import _get_random_text, create_dataset

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
class HomePageViewTest(ServerTestMixin, LiveServerTestCase):
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
        dataset = Dataset.objects.create(name=name, slug=name)
        # TODO: Replace with dataset.get_absolute_url() once implemented
        url = '/'
        response = self.client.get(reverse('bdr:home'))
        expected = '<a href="{url}">{title}</a>'.format(title=name, url=url)
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
        # TODO: Replace with category.get_absolute_url() once implemented
        category_url = "/"
        dataset = Dataset.objects.create(name=dataset_name, slug=dataset_name)
        # TODO: Replace with dataset.get_absolute_url() once implemented
        dataset_url = "/"
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
