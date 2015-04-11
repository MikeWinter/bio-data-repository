"""
The views for the Biological Data Repository front-end web application.

The following public classes are defined herein:
    HomePageView: Provides a list of recent updates, and a categorised listing of datasets.
    DatasetListView: Lists each dataset, its category and tag annotations, and the number of files associated with it.
    DatasetDetailView: Displays information about a dataset, including a list of its files and a link to the most
        recent revision.
    FileDetailView: Lists the revisions of a file, the modification dates, and links to download each version.
    RevisionDownloadView: Streams a compressed copy of the requested file to the client.
    SearchView: Displays groups lists of datasets, files and revisions that match search terms specified by the client.
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

import json

from django.db.models import Max
from django.http import HttpResponse
from django.views.generic import TemplateView

from .. import models


class HomePageView(TemplateView):
    """
    This view displays a list of recently updated files, and a categorised list of the datasets stored in the
    repository.

    This class extends the get_context_data method of the Django TemplateView class from which it inherits. For more
    information, see https://docs.djangoproject.com/en/1.6/ref/class-based-views/base/
    """
    template_name = 'frontend/home.html'
    """Defines the template file used to present the view."""

    def get_context_data(self, **kwargs):
        """Set up and return variables for use in the template for this view."""
        revisions = models.Revision.objects.fetch_all()
        datasets = models.Dataset.objects.filter(categories=None)
        context = super(HomePageView, self).get_context_data(**kwargs)
        context['dataset_list'] = {
            'subcategories': models.Category.objects.fetch_all().filter(parent=None),
            'datasets': datasets,
        }
        context['update_list'] = revisions.order_by('-updated_at')[:10]
        return context


class SearchView(TemplateView):
    """
    This view displays search results for datasets, files and revisions that match queried names and tags.

    This class extends the get_context_data method of the Django TemplateView class from which it inherits. For more
    information, see https://docs.djangoproject.com/en/1.6/ref/class-based-views/base/
    """
    template_name = 'frontend/search.html'
    """Defines the template file used to present the view."""

    def render_to_response(self, context, **response_kwargs):
        if not self.request.is_ajax():
            return super(SearchView, self).render_to_response(context, **response_kwargs)

        results = [{'name': obj.name, 'href': obj.get_absolute_url() if hasattr(obj, 'get_absolute_url') else None}
                   for name in ['datasets', 'files'] for obj in context[name] if obj is not None]
        return HttpResponse(json.dumps(results), content_type='application/json', **response_kwargs)

    def get_context_data(self, **kwargs):
        """
        Set up and return variables for use in the template for this view using the query parameter passed in a GET
        request.
        """
        context = super(SearchView, self).get_context_data(**kwargs)
        if self.request.method == 'GET' and 'query' in self.request.GET:
            query = self.request.GET['query']
            context['query'] = query

            if query:
                datasets = models.Dataset.objects.fetch_all()
                files = models.File.objects.fetch_all()
                revisions = models.Revision.objects.fetch_all().filter(tags__isnull=False)
                found_tag = False
                for token in query.split():
                    if token.startswith('#'):
                        found_tag = True
                        datasets = datasets.filter(tags__name__istartswith=token[1:])
                        files = files.filter(tags__name__istartswith=token[1:])
                        revisions = revisions.filter(tags__name__istartswith=token[1:])
                    else:
                        datasets = datasets.filter(name__icontains=token).annotate(
                            latest_revision=Max('file__revision__updated_at'))
                        files = files.filter(name__icontains=token)
                context['datasets'] = datasets
                context['files'] = files
                context['revisions'] = revisions if found_tag else []
        return context


class AboutView(TemplateView):
    template_name = 'frontend/about.html'


class LegalView(TemplateView):
    template_name = 'frontend/legal.html'
