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
import urlparse

from django.core.urlresolvers import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView, ListView
from django.views.generic.list import MultipleObjectMixin
import httplib2

from .. import app_settings, forms, models
from ..paginator import Paginator


class DatasetAddView(CreateView):
    model = models.Dataset
    form_class = forms.DatasetForm
    template_name = 'frontend/datasets/dataset_add.html'

    def get(self, request, *args, **kwargs):
        models.Tag.objects.fetch_all()
        models.Category.objects.fetch_all()
        return super(DatasetAddView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        url = urlparse.urljoin(app_settings.STORAGE_URL, 'datasets/')
        body = form.cleaned_data
        body.update(categories=[category.href for category in body['categories']],
                    tags=[tag.href for tag in body['tags']],
                    checked_at=None)
        response, content = httplib2.Http().request(url, method='POST', body=json.dumps(body),
                                                    headers={'Content-Type': 'application/json'})
        details = json.loads(content)
        if response.status != 201:
            return self.render_to_response(self.get_context_data(form=form, remote_errors=details['errors']))

        self.object = form.save(commit=False)
        _, _, self.object.href, _, _ = urlparse.urlsplit(response['location'])
        return super(DatasetAddView, self).form_valid(form)


class DatasetDeleteView(DeleteView):
    model = models.Dataset
    success_url = reverse_lazy('bdr.frontend:datasets')
    template_name = 'frontend/datasets/dataset_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        url = urlparse.urljoin(app_settings.STORAGE_URL, self.get_object().href)

        response, content = httplib2.Http().request(url, method='DELETE')
        return super(DatasetDeleteView, self).delete(request, *args, **kwargs)


class DatasetDetailView(MultipleObjectMixin, DetailView):
    """
    This view displays the details of a dataset, including a list of its files and links to the most recent revision of
    each file.
    """
    model = models.Dataset
    """Designate the model class used for obtaining data."""
    object_list = None
    paginate_by = 10
    paginate_orphans = 2
    paginator_class = Paginator
    template_name = 'frontend/datasets/dataset_detail.html'

    def get_object(self, queryset=None):
        obj = super(DatasetDetailView, self).get_object(queryset).fetch()
        self.object_list = obj.files.fetch_all()
        return obj

    def get_queryset(self):
        return self.model.objects.fetch_all()


class DatasetEditView(UpdateView):
    model = models.Dataset
    form_class = forms.DatasetForm
    template_name = 'frontend/datasets/dataset_edit.html'

    def form_valid(self, form):
        url = urlparse.urljoin(app_settings.STORAGE_URL, self.object.href)
        body = form.cleaned_data
        body.update(categories=[category.href for category in body['categories']],
                    tags=[tag.href for tag in body['tags']])
        response, content = httplib2.Http().request(url, method='PUT', body=json.dumps(body),
                                                    headers={'Content-Type': 'application/json'})
        return super(DatasetEditView, self).form_valid(form) if response.status == 200 else self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(DatasetEditView, self).get_context_data(**kwargs)
        context['tags'] = models.Tag.objects.fetch_all()
        return context


class DatasetListView(ListView):
    """This view displays a list of datasets stored in the repository."""
    model = models.Dataset
    paginate_by = 10
    paginate_orphans = 2
    paginator_class = Paginator
    template_name = 'frontend/datasets/dataset_list.html'

    context_object_name = 'datasets'
    """Set the template variable name used to access the QuerySet result during rendering."""

    def get_queryset(self):
        return self.model.objects.fetch_all()
