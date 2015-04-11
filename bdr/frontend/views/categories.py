import json
import urlparse

from django.core.urlresolvers import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView, ListView
import httplib2
from restless.models import serialize

from ..paginator import Paginator
from .. import app_settings
from .. import forms
from .. import models


class CategoryAddView(CreateView):
    model = models.Category
    form_class = forms.CategoryForm
    template_name = 'frontend/categories/category_add.html'

    def form_valid(self, form):
        url = urlparse.urljoin(app_settings.STORAGE_URL, 'categories/')
        body = serialize(form.cleaned_data, exclude=['parent', 'href'])
        response, content = httplib2.Http().request(url, method='POST', body=json.dumps(body),
                                                    headers={'Content-Type': 'application/json'})
        if response.status != 201:
            details = json.loads(content)
            return self.render_to_response(self.get_context_data(form=form, remote_errors=details['errors']))
        return super(CategoryAddView, self).form_valid(form)


class CategoryDeleteView(DeleteView):
    model = models.Category
    success_url = reverse_lazy('bdr.frontend:categories')
    template_name = 'frontend/categories/category_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        url = urlparse.urljoin(app_settings.STORAGE_URL, self.get_object().href)

        response, content = httplib2.Http().request(url, method='DELETE')
        return super(CategoryDeleteView, self).delete(request, *args, **kwargs)


class CategoryDetailView(DetailView):
    model = models.Category
    template_name = 'frontend/categories/category_detail.html'

    def get_queryset(self):
        return self.model.objects.fetch_all()


class CategoryEditView(UpdateView):
    model = models.Category
    form_class = forms.CategoryForm
    template_name = 'frontend/categories/category_edit.html'

    def form_valid(self, form):
        url = urlparse.urljoin(app_settings.STORAGE_URL, self.object.href)
        body = serialize(form.cleaned_data, exclude=['parent', 'href'])

        response, content = httplib2.Http().request(url, method='PUT', body=json.dumps(body),
                                                    headers={'Content-Type': 'application/json'})
        return super(CategoryEditView, self).form_valid(form) if response.status == 200 else self.form_invalid(form)


class CategoryListView(ListView):
    context_object_name = 'categories'
    model = models.Category
    paginate_by = 10
    paginate_orphans = 2
    paginator_class = Paginator
    template_name = 'frontend/categories/category_list.html'

    def get_queryset(self):
        self.model.objects.fetch_all()
        return self._get_children(parent=None)

    def _get_children(self, parent):
        parents = self.model.objects.filter(parent=parent)
        categories = []
        for parent in parents:
            categories.append(parent)
            categories.extend(self._get_children(parent))
        return categories
