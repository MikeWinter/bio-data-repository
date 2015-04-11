import json
import os
import urllib2
import urlparse

from django.http import Http404, StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.gzip import gzip_page
from django.views.generic import FormView
from django.views.generic.detail import SingleObjectMixin

from .. import app_settings, formsets, models


class RevisionDownloadView(SingleObjectMixin, FormView):
    """
    This view streams a compressed file to the client.

    File compression is performed on the fly.

    This class overrides the get_object method of the Django SingleObjectMixin class. For more information see
    https://docs.djangoproject.com/en/1.6/ref/class-based-views/mixins-single-object/#django.views.generic.detail.SingleObjectMixin
    """
    form_class = formsets.FieldSelectionListFormSet
    model = models.Revision
    """Designate the model class used for obtaining data."""
    slug_field = 'level'
    slug_url_kwarg = 'rev'
    template_name = 'frontend/revisions/export.html'

    def __init__(self, **kwargs):
        super(RevisionDownloadView, self).__init__(**kwargs)
        self._dataset = None
        self.object = None

    @method_decorator(gzip_page)
    def get(self, *args, **kwargs):
        """Respond to a GET request by streaming the requested file to the client, compressing on-the-fly."""
        self.model.objects.fetch_all()
        self.object = self.get_object()
        return super(RevisionDownloadView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        return super(RevisionDownloadView, self).post(*args, **kwargs)

    def form_valid(self, form):
        url = urlparse.urljoin(app_settings.STORAGE_URL, self.object.href)
        data = {'fields': [item['name'] for item in form.get_selected()]}
        request = urllib2.urlopen(urllib2.Request(url + '/data', json.dumps(data),
                                                  {'Content-Type': 'application/json'}))

        response = StreamingHttpResponse(request, content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(self.object.file.name)
        return response

    def get_context_data(self, **kwargs):
        context = super(RevisionDownloadView, self).get_context_data(**kwargs)
        context['dataset'] = self._dataset
        context['formset'] = context.pop('form')
        return context

    def get_form_kwargs(self):
        kwargs = super(RevisionDownloadView, self).get_form_kwargs()
        kwargs.update(queryset=models.FormatField.objects.filter(format=self.object.format))
        return kwargs

    def get_object(self, queryset=None):
        """
        Get the revision object to be streamed by this view.

        If this view is not invoked with either the primary key, or the dataset slug, file name and revision number, an
        exception will be raised.

        :param queryset: the QuerySet used to obtain objects from the database (default None)
        """
        if queryset is None:
            queryset = self.get_queryset()
        if self.kwargs.get(self.slug_url_kwarg) == 'latest':
            obj = queryset.first()
            if obj is None:
                raise Http404("No revisions exist for this file.")
        else:
            obj = super(RevisionDownloadView, self).get_object(queryset)
        return obj

    def get_queryset(self):
        queryset = super(RevisionDownloadView, self).get_queryset()
        self._dataset = models.Dataset.objects.get(slug=self.kwargs.get('ds'))
        filename = self.kwargs.get('fn')
        return queryset.filter(file__name=filename, file__dataset=self._dataset)
