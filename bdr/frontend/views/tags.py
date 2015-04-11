import json
import urlparse

from django.core.urlresolvers import reverse_lazy
from django.db.models.aggregates import Max, Count
from django.http import HttpResponse
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView, ListView
import httplib2
from restless.models import serialize

from .. import models, forms, app_settings
from ..paginator import Paginator


class TagAddView(CreateView):
    model = models.Tag
    form_class = forms.TagForm
    success_url = reverse_lazy('bdr.frontend:tags')
    template_name = 'frontend/tags/tag_add.html'

    def form_valid(self, form):
        url = urlparse.urljoin(app_settings.STORAGE_URL, 'tags/')
        body = serialize(form.cleaned_data, exclude=['parent', 'href'])
        response, content = httplib2.Http().request(url, method='POST', body=json.dumps(body),
                                                    headers={'Content-Type': 'application/json'})
        if response.status != 201:
            details = json.loads(content)
            return self.render_to_response(self.get_context_data(form=form, remote_errors=details['errors']))
        return super(TagAddView, self).form_valid(form)


class TagDeleteView(DeleteView):
    model = models.Tag
    slug_field = 'name'
    slug_url_kwarg = 'name'
    success_url = reverse_lazy('bdr.frontend:tags')
    template_name = 'frontend/tags/tag_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        url = urlparse.urljoin(app_settings.STORAGE_URL, self.get_object().href)

        response, content = httplib2.Http().request(url, method='DELETE')
        return super(TagDeleteView, self).delete(request, *args, **kwargs)


class TagDetailView(DetailView):
    """
    This view displays the datasets, files and revisions associated with a given tag.

    This class extends the get_context_data method of the Django TemplateView class from which it inherits. For more
    information, see https://docs.djangoproject.com/en/1.6/ref/class-based-views/base/
    """
    model = models.Tag
    slug_field = 'name'
    slug_url_kwarg = 'name'
    template_name = 'frontend/tags/tag_detail.html'
    """Defines the template file used to present the view."""

    def get_context_data(self, **kwargs):
        """
        Set up and return variables for use in the template for this view.
        """
        context = super(TagDetailView, self).get_context_data(**kwargs)
        context.update(
            datasets=models.Dataset.objects.fetch_all().filter(tags__name=self.object.name).annotate(
                file_count=Count('file'), latest_revision=Max('file__revision__updated_at')),
            files=models.File.objects.fetch_all().filter(tags__name=self.object.name),
            revisions=models.Revision.objects.fetch_all().filter(tags__name=self.object.name))
        return context


class TagEditView(UpdateView):
    model = models.Tag
    form_class = forms.TagForm
    slug_field = 'name'
    slug_url_kwarg = 'name'
    success_url = reverse_lazy('bdr.frontend:tags')
    template_name = 'frontend/tags/tag_edit.html'

    def form_valid(self, form):
        url = urlparse.urljoin(app_settings.STORAGE_URL, self.object.href)
        body = serialize(form.cleaned_data, exclude=['parent', 'href'])

        response, content = httplib2.Http().request(url, method='PUT', body=json.dumps(body),
                                                    headers={'Content-Type': 'application/json'})
        return super(TagEditView, self).form_valid(form) if response.status == 200 else self.form_invalid(form)


class TagListView(ListView):
    context_object_name = 'tags'
    model = models.Tag
    paginate_by = 10
    paginate_orphans = 2
    paginator_class = Paginator
    template_name = 'frontend/tags/tag_list.html'

    def get(self, request, *args, **kwargs):
            return super(TagListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = self.model.objects.fetch_all()

        if self.request.method == 'GET' and 'filter' in self.request.GET:
            query = self.request.GET['filter']
            matched = False
            for token in query.split():
                if token.startswith('#'):
                    matched = True
                    queryset = queryset.filter(name__istartswith=token[1:])
            if not matched:
                queryset = queryset.none()
        return queryset

    def render_to_response(self, context, **response_kwargs):
        if not self.request.is_ajax():
            return super(TagListView, self).render_to_response(context, **response_kwargs)

        results = [{'name': '#%s' % obj.name, 'href': None} for obj in context['tags']]
        return HttpResponse(json.dumps(results), content_type='application/json', **response_kwargs)