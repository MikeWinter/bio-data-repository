import json
import urlparse
import os

from django.contrib.formtools.wizard.views import SessionWizardView
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import default_storage
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.views.generic import DetailView
from django.views.generic.list import MultipleObjectMixin
import httplib2

from .. import app_settings, forms, formsets, models
from ..paginator import Paginator
from ...utils.archives import Archive


class FileAddView(SessionWizardView):
    # TODO: Skip file selection when uploading either a single file or an archive with only one member.
    file_storage = default_storage
    form_list = [
        ('upload', forms.FileUploadForm),
        ('selection', formsets.ArchiveMemberSelectionFormSet),
        ('details', formsets.FileListFormSet),
    ]
    templates = {
        'upload': 'frontend/files/file_add.html',
        'selection': 'frontend/files/file_selection.html',
        'details': 'frontend/files/file_edit.html',
    }

    def done(self, form_list, **kwargs):
        details = form_list[-1]
        url = urlparse.urljoin(app_settings.STORAGE_URL, self._get_dataset().href + '/')
        files = self.get_form_step_files(form_list[self.get_step_index('upload')])

        for form in details.forms:
            instance = self._save_form(form, url)
            field_name = '%s-%s' % (self.get_form_prefix('upload', instance), 'new_file')
            self._save_revision(instance, files[field_name])

        for field in files:
            filename = files[field]
            files[field].close()
            self.file_storage.delete(filename)
        return HttpResponseRedirect(reverse('bdr.frontend:dataset-detail', kwargs={'slug': self.kwargs['slug']}))

    def get(self, request, *args, **kwargs):
        models.Format.objects.fetch_all()
        models.Tag.objects.fetch_all()
        models.Dataset.objects.fetch_all()
        models.File.objects.fetch_all()
        return super(FileAddView, self).get(request, *args, **kwargs)

    def get_context_data(self, form, **kwargs):
        context = super(FileAddView, self).get_context_data(form, **kwargs)
        context['dataset'] = self._get_dataset()
        return context

    def get_form_initial(self, step):
        if step == 'selection':
            data = self.get_cleaned_data_for_step('upload')
            uploaded_file = data.get('new_file')
            path = os.path.join(app_settings.settings.MEDIA_ROOT, uploaded_file.name)
            archive = Archive.instance(uploaded_file, path)
            return [{'name': member} for member in archive]
        elif step == 'details':
            instances = models.File.objects.filter(dataset=self._get_dataset())
            existing_names = [instance['name'] for instance in instances.values('name')]
            files = [selected for selected in self._get_selected_files() if selected['name'] not in existing_names]
            return files
        return super(FileAddView, self).get_form_initial(step)

    def get_form_instance(self, step):
        if step == 'details':
            instances = models.File.objects.filter(dataset=self._get_dataset(),
                                                   name__in=[item['name'] for item in self._get_selected_files()])
            return instances
        return super(FileAddView, self).get_form_instance(step)

    def get_form(self, step=None, *args, **kwargs):
        form = super(FileAddView, self).get_form(step, *args, **kwargs)
        if step == 'details':
            form.extra = len(self.get_form_initial(step))
        return form

    def get_template_names(self):
        return self.templates[self.steps.current]

    def _get_dataset(self):
        return models.Dataset.objects.get(slug=self.kwargs['slug'])

    def _get_selected_files(self):
        files = self.get_cleaned_data_for_step('selection')
        dataset = self._get_dataset()
        return [{'name': item['name'], 'dataset': dataset} for item in files if item['selected']]

    def _save_revision(self, model_instance, file_):
        path = os.path.join(app_settings.settings.MEDIA_ROOT, file_.name)
        archive = Archive.instance(file_, path)
        member = archive[model_instance.name]
        body = {'size': member.size, 'updated_at': member.mtime, 'tags': []}
        url = urlparse.urljoin(app_settings.STORAGE_URL, model_instance.href + '/')
        response, content = httplib2.Http().request(url, method='POST',
                                                    body=json.dumps(body, cls=DjangoJSONEncoder),
                                                    headers={'Content-Type': 'application/json'})
        httplib2.Http().request(response['location'] + '/data', method='PUT', body=member.data,
                                headers={'Content-Type': 'application/octet-stream',
                                         'Content-Length': str(member.size)})

    def _save_form(self, form, url):
        method = 'POST'
        body = {'name': form.cleaned_data['name'],
                'default_format': form.cleaned_data['default_format'].href,
                'tags': [tag.href for tag in form.cleaned_data['tags']]}
        if form.cleaned_data['href']:
            method = 'PUT'
            relative_url = form.cleaned_data['href']
            if isinstance(relative_url, models.File):
                relative_url = relative_url.href
            url = urlparse.urljoin(app_settings.STORAGE_URL, relative_url)
        response, _ = httplib2.Http().request(url, method=method, body=json.dumps(body),
                                              headers={'Content-Type': 'application/json'})
        instance = form.save(commit=False)
        _, _, instance.href, _, _ = urlparse.urlsplit(response['location'])
        instance.save()
        form.save_m2m()
        return instance


class FileDetailView(MultipleObjectMixin, DetailView):
    """
    This view displays information about a given file, including a list of its revisions and links for downloading their
    content.

    This class overrides the get_object method of the Django DetailView class. For more information see
    https://docs.djangoproject.com/en/1.6/ref/class-based-views/generic-display/
    """
    model = models.File
    """Designate the model class used for obtaining data."""
    paginate_by = 10
    paginate_orphans = 2
    paginator_class = Paginator
    template_name = 'frontend/files/file_detail.html'

    def get_object(self, queryset=None):
        """
        Get the file object to be displayed by this view.

        If this view is not invoked with either the primary key, or the dataset slug and file name, an exception will be
        raised.
        """
        if queryset is None:
            queryset = self.get_queryset()

        ds = self.kwargs.get('ds', None)
        fn = self.kwargs.get('fn', None)
        if ds is not None and fn is not None:
            queryset = queryset.filter(name=fn, dataset__slug=ds)
        else:
            raise AttributeError("File view must be called with a file name and the slug for its containing"
                                 " dataset.")
        try:
            obj = queryset.get().fetch()
        except ObjectDoesNotExist:
            raise Http404("No files found matching the query.")
        self.object_list = obj.revisions.fetch_all()
        return obj

    def get_queryset(self):
        return self.model.objects.fetch_all()