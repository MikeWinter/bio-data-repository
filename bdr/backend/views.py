"""Defines the various views for the API server."""

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

from hashlib import sha1
import json
import os
import stat
import tempfile

from django.db import transaction
from django.forms.models import modelform_factory
from django.http.response import HttpResponse, StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.gzip import gzip_page
from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin
from restless.http import Http200, Http201, Http404, HttpError
from restless.modelviews import DetailEndpoint, ListEndpoint
from restless.models import serialize
import xdelta

from . import app_settings, formats, forms, models


_HREF = ('href', lambda o: o.get_absolute_url())
_PARENT = ('parent', lambda o: None if o.parent is None else o.parent.get_absolute_url())
_FILE_COUNT = ('files', lambda o: o.files.count())
_REVISION_COUNT = ('revisions', lambda o: o.revisions.count())

_TAG_REF = {'fields': ['name', _HREF]}
_CATEGORY_REF = {'fields': ['name', _HREF, 'slug', _PARENT]}
_FORMAT_REF = {'fields': ['name', _HREF, 'slug']}
_DATASET_REF = {'fields': ['name', _HREF, 'slug', _FILE_COUNT, ('categories', _CATEGORY_REF), ('tags', _TAG_REF)]}
_FILE_REF = {
    'fields': ['name', _HREF, _REVISION_COUNT, ('default_format', lambda o: o.default_format.get_absolute_url()),
               ('tags', _TAG_REF)]}
_REVISION_REF = {'fields': [('revision', lambda o: o.level), _HREF, ('format', lambda o: o.format.get_absolute_url()),
                            'size', 'updated_at', ('tags', _TAG_REF)]}


class DatasetCollectionView(ListEndpoint):
    form = forms.DatasetForm
    model = models.Dataset

    def post(self, request, *args, **kwargs):
        """Create a new dataset."""
        form = self.form(request.data, request.FILES)

        if form.is_valid():
            obj = form.save()
            response = Http201(serialize(obj, **_DATASET_REF))
            response['Location'] = obj.get_absolute_url()
            return response

        raise HttpError(400, 'Invalid Data', errors=form.errors)

    def serialize(self, objects):
        return serialize({'datasets': objects}, **_DATASET_REF)


class DatasetDetailView(DetailEndpoint):
    # TODO: Cascading deletion
    form = forms.DatasetForm
    lookup_field = 'slug'
    model = models.Dataset

    def serialize(self, obj):
        return serialize(obj, fields=['name', 'slug', _HREF, 'notes', ('categories', _CATEGORY_REF), ('tags', _TAG_REF),
                                      'update_uri', 'update_username', 'update_password', 'update_frequency',
                                      'updated_at', ('files', _FILE_REF)])


class DatasetFilesCollectionView(ListEndpoint):
    form = forms.FileForm
    model = models.File

    def get_query_set(self, request, *args, **kwargs):
        return super(DatasetFilesCollectionView, self).get_query_set(request, *args, **kwargs).filter(
            dataset__slug=kwargs['ds'])

    def post(self, request, *args, **kwargs):
        """Create a new object."""
        data = request.data
        if data is not None:
            data = dict(data)
            data.update(dataset=models.Dataset.objects.get(slug=kwargs['ds']).pk)
        form = self.form(data, request.FILES)

        if form.is_valid():
            obj = form.save()
            response = Http201(serialize(obj, **_FILE_REF))
            response['Location'] = obj.get_absolute_url()
            return response

        raise HttpError(400, 'Invalid Data', errors=form.errors)

    def serialize(self, objects):
        return serialize({'files': objects}, **_FILE_REF)


class FileCollectionView(ListEndpoint):
    model = models.File

    def serialize(self, objects):
        fields = _FILE_REF['fields']
        fields.append(('dataset', lambda o: o.dataset.get_absolute_url()))
        return serialize({'files': objects}, fields=fields)


class FileDetailView(DetailEndpoint):
    # TODO: Cascading deletion
    form = forms.FileForm
    model = models.File

    def get_instance(self, request, *args, **kwargs):
        ds = kwargs.get('ds', None)
        fn = kwargs.get('fn', None)
        if ds is not None and fn is not None:
            queryset = self.model.objects.filter(name=fn, dataset__slug=ds)
        else:
            raise HttpError(404, "File view must be requested with a file name and the slug identifying its containing"
                                 " dataset.")
        try:
            return queryset.get()
        except self.model.DoesNotExist:
            raise HttpError(404, 'Resource Not Found')

    def put(self, request, *args, **kwargs):
        """Update the file represented by this endpoint."""

        data = request.data
        if data is not None:
            data = dict(data)
            data.update(dataset=models.Dataset.objects.get(slug=kwargs['ds']).pk)
        instance = self.get_instance(request, *args, **kwargs)
        form = self.form(data, request.FILES, instance=instance)

        if form.is_valid():
            obj = form.save()
            response = Http200(self.serialize(obj))
            response['Location'] = obj.get_absolute_url()
            return response
        raise HttpError(400, 'Invalid data', errors=form.errors)

    def serialize(self, obj):
        return serialize(obj, fields=['name', _HREF, ('default_format', lambda o: o.default_format.get_absolute_url()),
                                      ('tags', _TAG_REF), ('revisions', _REVISION_REF)])


class FileRevisionsCollectionView(ListEndpoint):
    form = forms.RevisionForm
    model = models.Revision

    def get_query_set(self, request, *args, **kwargs):
        return super(FileRevisionsCollectionView, self).get_query_set(request, *args, **kwargs).filter(
            file__name=kwargs['fn'], file__dataset__slug=kwargs['ds'])

    def post(self, request, *args, **kwargs):
        """Create a new object."""
        data = request.data
        file = models.File.objects.get(name=kwargs['fn'], dataset__slug=kwargs['ds'])
        level = 1
        latest = models.Revision.objects.filter(file=file).first()
        if latest:
            level += latest.level
        if data is not None:
            data.update(level=level, file=file.pk, format=file.default_format.pk)
        form = self.form(data, request.FILES)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.level = level
            if data:
                obj.updated_at = data['updated_at']
                obj.size = data['size']
            obj.save()
            form.save_m2m()

            response = Http201(serialize(obj, **_REVISION_REF))
            response['Location'] = obj.get_absolute_url()
            return response

        raise HttpError(400, 'Invalid Data', errors=form.errors)

    def serialize(self, objects):
        return serialize({'revisions': objects}, **_REVISION_REF)


class RevisionCollectionView(ListEndpoint):
    model = models.Revision

    def serialize(self, objects):
        fields = _REVISION_REF['fields']
        fields.append(('file', lambda o: o.file.get_absolute_url()))
        return serialize({'revisions': objects}, fields=fields)


class RevisionDetailView(DetailEndpoint):
    # TODO: Deletion and recoding
    model = models.Revision

    def get_instance(self, request, *args, **kwargs):
        ds = kwargs.get('ds', None)
        fn = kwargs.get('fn', None)
        rev = kwargs.get('rev', None)
        if ds is not None and fn is not None and rev is not None:
            queryset = self.model.objects.filter(level=rev, file__name=fn, file__dataset__slug=ds)
        else:
            raise HttpError(404, "Revision view must be requested with a revision number, file name and the slug"
                                 " identifying its containing dataset.")
        try:
            return queryset.get()
        except self.model.DoesNotExist:
            raise HttpError(404, 'Resource Not Found')

    def serialize(self, obj):
        return serialize(obj, fields=[('revision', lambda o: o.level), _HREF, 'size', 'updated_at',
                                      ('format', lambda o: o.format.get_absolute_url()), ('tags', _TAG_REF)])


class ExportView(SingleObjectMixin, View):
    """
    This view streams a compressed file to the client.

    File compression is performed on the fly.

    This class overrides the get_object method of the Django SingleObjectMixin class. For more information see
    https://docs.djangoproject.com/en/1.6/ref/class-based-views/mixins-single-object/#django.views.generic.detail.SingleObjectMixin
    """
    model = models.Revision
    """Designate the model class used for obtaining data."""

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ExportView, self).dispatch(request, *args, **kwargs)

    @method_decorator(gzip_page)
    def post(self, request, *args, **kwargs):
        """Respond to a GET request by streaming the requested file to the client, compressing on-the-fly."""
        request_data = request.read()
        format_spec = json.loads(request_data) if request_data else {}

        revision = self.get_object()
        try:
            fp = open(self._get_path(revision), 'rb')
        except IOError:
            return Http404("File not found")
        delta = xdelta.DeltaFile(fp)
        delta.source = self._decode_chain(revision.get_previous())

        reader = formats.Reader.instance(delta, revision.format)
        converter = formats.Converter.instance(reader, revision.format, format_spec.get('fields', []))

        response = StreamingHttpResponse(converter, content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(revision.file.name)
        return response

    def put(self, *args, **kwargs):
        revision = self.get_object()
        filename = self._get_path(revision)

        path = os.path.dirname(filename)
        if not os.path.exists(path):
            os.makedirs(path, stat.S_IWUSR | stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP
                        | stat.S_IROTH | stat.S_IXOTH)

        # Dump uploaded data to raw file
        fp = tempfile.TemporaryFile()
        while True:
            chunk = self.request.read(8 * 1024 * 1024)
            if not chunk:
                break
            fp.write(chunk)
        fp.seek(0)

        # Decode previous file to raw
        preceding_revision = revision.get_previous()
        if preceding_revision:
            preceding_file = self._decode_chain(preceding_revision)
            chain_args = (preceding_revision.level, preceding_file)
        else:
            preceding_file = None
            chain_args = ()

        # Decode next file to raw
        next_revision = revision.get_next()
        if next_revision:
            next_file = self._decode_chain(next_revision, *chain_args)

            # Recode next file using raw self
            with xdelta.DeltaFile(open(self._get_path(next_revision), 'wb')) as delta:
                delta.source = fp
                while True:
                    chunk = next_file.read(8 * 1024 * 1024)
                    if not chunk:
                        break
                    delta.write(chunk)
            fp.seek(0)
            # Delete next raw
            del next_file

        # Encode self using previous raw
        with xdelta.DeltaFile(open(filename, 'wb')) as delta:
            os.fchmod(delta.fileno(), stat.S_IWUSR | stat.S_IRUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
            delta.source = preceding_file
            while True:
                chunk = fp.read(8 * 1024 * 1024)
                if not chunk:
                    break
                delta.write(chunk)

        return HttpResponse(status=204)

    def get_object(self, queryset=None):
        """
        Get the revision object to be streamed by this view.

        If this method does not receive either the primary key, or the dataset slug, file name and revision number, an
        exception will be raised.

        :param queryset: the QuerySet used to obtain objects from the database (default None)
        """
        if queryset is None:
            queryset = self.get_queryset()

        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk is not None:
            queryset = queryset.filter(pk=pk)
        else:
            ds = self.kwargs.get('ds', None)
            fn = self.kwargs.get('fn', None)
            rev = self.kwargs.get('rev', None)
            if ds is not None and fn is not None and rev is not None:
                queryset = queryset.filter(level=rev, file__name=fn, file__dataset__slug=ds)
            else:
                raise AttributeError("Revision view must be called with a revision number, file name and the slug for"
                                     " the containing dataset.")

        from django.http import Http404
        from django.core.exceptions import ObjectDoesNotExist

        try:
            obj = queryset.get()
        except ObjectDoesNotExist:
            raise Http404("No revisions found matching the query.")
        return obj

    @staticmethod
    def _get_path(revision):
        file = revision.file
        filename = '%s.%i.diff' % (sha1(file.name).hexdigest(), revision.level)
        return os.path.join(app_settings.STORAGE_ROOT, file.dataset.slug, filename)

    def _decode_chain(self, revision, start=-1, base=None):
        fp = base
        if revision:
            qs = models.Revision.objects.filter(file=revision.file)
            if start == -1:
                start = qs.first().level
            for rev in qs.filter(level__range=(revision.level, start)):
                path = self._get_path(rev)
                if not os.path.exists(path):
                    continue
                src = xdelta.DeltaFile(open(path, 'rb'))
                src.source = fp
                tgt = tempfile.TemporaryFile()
                for chunk in src.chunks():
                    tgt.write(chunk)
                src.close()
                fp = tgt
                fp.seek(0)
        return fp


class FormatCollectionView(ListEndpoint):
    model = models.Format

    def post(self, request, *args, **kwargs):
        form = modelform_factory(self.model)(request.data or None, request.FILES)
        field_form_type = modelform_factory(models.FormatField, exclude=['type'])

        if form.is_valid():
            obj = form.save()
            for index, field in enumerate(request.data.get('fields')):
                field.update(ordinal=index, format=obj.pk)
                field_form = field_form_type(field)
                if not field_form.is_valid():
                    break

                field_form.save()
            else:
                response = Http201(self.serialize(obj))
                response['Location'] = obj.get_absolute_url()
                return response

        raise HttpError(400, 'Invalid Data', errors=form.errors)

    def serialize(self, objects):
        return serialize({'formats': objects}, **_FORMAT_REF)


class FormatDetailView(DetailEndpoint):
    lookup_field = 'slug'
    model = models.Format

    def put(self, request, *args, **kwargs):
        instance = self.get_instance(request, *args, **kwargs)

        with transaction.atomic():
            form = modelform_factory(self.model)(request.data or None, request.FILES, instance=instance)
            field_form_type = modelform_factory(models.FormatField, exclude=['type'])

            if form.is_valid():
                obj = form.save()
                models.FormatField.objects.filter(format=obj).delete()
                for index, field in enumerate(request.data.get('fields')):
                    field.update(ordinal=index, format=obj.pk)
                    field_form = field_form_type(field)
                    if not field_form.is_valid():
                        break

                    field_form.save()
                else:
                    response = Http200(self.serialize(obj))
                    response['Location'] = obj.get_absolute_url()
                    return response

            raise HttpError(400, 'Invalid Data', errors=form.errors)

    def serialize(self, obj):
        return serialize(obj, fields=['name', _HREF, 'slug', 'module', 'separator', 'comment', 'quote',
                                      ('fields', {'fields': ['name', 'is_key', 'ordinal']})])


class CategoryCollectionView(ListEndpoint):
    form = forms.CategoryForm
    model = models.Category

    def get_query_set(self, request, *args, **kwargs):
        return self._get_children(None)

    def serialize(self, objects):
        return serialize({'categories': objects}, **_CATEGORY_REF)

    def _get_children(self, parent):
        categories = []
        for category in self.model.objects.filter(parent=parent):
            categories.append(category)
            categories.extend(self._get_children(category))
        return categories


class CategoryDetailView(DetailEndpoint):
    lookup_field = 'slug'
    model = models.Category

    def delete(self, request, *args, **kwargs):
        category = self.get_instance(request, *args, **kwargs)
        parent = category.parent
        subcategories = self.model.objects.filter(parent=category)
        for subcategory in subcategories:
            subcategory.parent = parent
            subcategory.save()
        datasets = category.datasets.all()
        for dataset in datasets:
            dataset.categories.remove(category)
            if parent is not None:
                dataset.categories.add(parent)
        return super(CategoryDetailView, self).delete(request, *args, **kwargs)

    def serialize(self, obj):
        return serialize(obj, fields=['name', _HREF, 'slug', _PARENT, ('subcategories', _CATEGORY_REF),
                                      ('datasets', _DATASET_REF)])


class TagCollectionView(ListEndpoint):
    form = forms.TagForm
    model = models.Tag

    def serialize(self, objects):
        return serialize({'tags': objects}, **_TAG_REF)


class TagDetailView(DetailEndpoint):
    model = models.Tag

    def serialize(self, obj):
        return serialize(obj, fields=['name', _HREF, ('datasets', _DATASET_REF), ('files', _FILE_REF),
                                      ('revisions', _REVISION_REF)])
