import json
import urlparse

from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from restless.models import serialize
import httplib2

from .. import app_settings, forms, models
from ..formsets import FormatFieldInlineFormSet
from ..paginator import Paginator


class FormatAddView(CreateView):
    model = models.Format
    form_class = forms.FormatForm
    template_name = 'frontend/formats/format_add.html'

    def __init__(self, **kwargs):
        super(FormatAddView, self).__init__(**kwargs)
        self._fieldset = None
        self.object = None

    def get(self, request, *args, **kwargs):
        self._fieldset = FormatFieldInlineFormSet()
        return super(FormatAddView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self._fieldset = FormatFieldInlineFormSet(data=request.POST)
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if request.POST.get('operation') == 'add':
            self._fieldset.add_extra_form()
            return self.form_invalid(form)

        if self._fieldset.is_valid() and form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(FormatAddView, self).get_context_data(**kwargs)
        context['formset'] = self._fieldset
        return context

    def form_valid(self, form):
        url = urlparse.urljoin(app_settings.STORAGE_URL, 'formats/')
        body = serialize(form.cleaned_data, exclude=['href'])
        body.update(module=self.model.MODULE_NAME)
        body.update(fields=[{'name': field['name'], 'is_key': field['is_key']}
                            for field in self._fieldset.cleaned_data if field and not field.get('DELETE')])
        response, content = httplib2.Http().request(url, method='POST', body=json.dumps(body),
                                                    headers={'Content-Type': 'application/json'})
        if response.status != 201:
            details = json.loads(content)
            return self.render_to_response(self.get_context_data(form=form, remote_errors=details['errors']))

        self.object = form.save(commit=False)
        _, _, self.object.href, _, _ = urlparse.urlsplit(response['location'])
        self.object.module = self.model.MODULE_NAME
        result = super(FormatAddView, self).form_valid(form)
        self._fieldset.save_new(form)
        return result


class FormatDeleteView(DeleteView):
    model = models.Format
    success_url = reverse_lazy('bdr.frontend:formats')
    template_name = 'frontend/formats/format_confirm_delete.html'

    def get(self, *args, **kwargs):
        object = self.get_object()
        if not object.can_edit:
            return HttpResponseRedirect(object.get_absolute_url())
        return super(FormatDeleteView, self).get(*args, **kwargs)

    def delete(self, request, *args, **kwargs):
        object = self.get_object()
        if not object.can_edit:
            return HttpResponseRedirect(object.get_absolute_url())

        url = urlparse.urljoin(app_settings.STORAGE_URL, object.href)

        response, content = httplib2.Http().request(url, method='DELETE')
        return super(FormatDeleteView, self).delete(request, *args, **kwargs)


class FormatDetailView(DetailView):
    model = models.Format
    template_name = 'frontend/formats/format_detail.html'

    def get_context_data(self, **kwargs):
        context = super(FormatDetailView, self).get_context_data(**kwargs)
        context['fields'] = models.FormatField.objects.filter(format=self.object)
        return context

    def get_object(self, queryset=None):
        return super(FormatDetailView, self).get_object(queryset).fetch()

    def get_queryset(self):
        return self.model.objects.fetch_all()


class FormatEditView(UpdateView):
    model = models.Format
    form_class = forms.FormatForm
    template_name = 'frontend/formats/format_edit.html'
    
    def __init__(self, **kwargs):
        super(FormatEditView, self).__init__(**kwargs)
        self._fieldset = None
        self.object = None

    def get(self, request, *args, **kwargs):
        models.Format.objects.fetch_all()
        object = self.get_object()
        if not object.can_edit:
            return HttpResponseRedirect(object.get_absolute_url())

        self._fieldset = FormatFieldInlineFormSet(instance=object)
        self._fieldset.extra = 1
        response = super(FormatEditView, self).get(request, *args, **kwargs)
        return response

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.can_edit:
            return HttpResponseRedirect(self.object.get_absolute_url())

        self._fieldset = FormatFieldInlineFormSet(data=request.POST, instance=self.object)
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if request.POST.get('operation') == 'add':
            self._fieldset.add_extra_form()
            return self.form_invalid(form)

        if form.is_valid() and self._fieldset.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(FormatEditView, self).get_context_data(**kwargs)
        context['formset'] = self._fieldset
        return context

    def get_object(self, queryset=None):
        return super(FormatEditView, self).get_object(queryset).fetch()

    def form_valid(self, form):
        url = urlparse.urljoin(app_settings.STORAGE_URL, self.object.href)
        body = serialize(form.cleaned_data, exclude=['href'])
        body.update(fields=[{'name': field['name'], 'is_key': field['is_key']}
                            for field in self._fieldset.cleaned_data if field and not field['DELETE']])
        response, content = httplib2.Http().request(url, method='PUT', body=json.dumps(body),
                                                    headers={'Content-Type': 'application/json'})
        if response.status != 200:
            return self.form_invalid(form)

        redirect = super(FormatEditView, self).form_valid(form)
        self._fieldset.save_existing_objects()
        self._fieldset.save_new(form)
        return redirect


class FormatListView(ListView):
    """This view displays a list of formats describing files in the repository."""
    model = models.Format
    paginate_by = 10
    paginate_orphans = 2
    paginator_class = Paginator
    template_name = 'frontend/formats/format_list.html'

    context_object_name = 'formats'
    """Set the template variable name used to access the QuerySet result during rendering."""

    def get_queryset(self):
        return self.model.objects.fetch_all()