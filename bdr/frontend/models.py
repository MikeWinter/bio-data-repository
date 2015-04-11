"""
The models for the Biological Data Repository front-end web application.

The following public classes are defined herein:
    Category: Represents categories used to organise datasets.
    Tag: Represents tags used to annotate datasets, files and revisions.
    Dataset: Represents datasets maintained by this repository.
    File: Represents files maintained by this repository.
    Revision: Represents revisions of files maintained by this repository.
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
import threading
import urlparse

from django.core.urlresolvers import reverse
from django.db import models
import httplib2

from . import app_settings


class RemoteManager(models.Manager):
    client = httplib2.Http(app_settings.CACHE_ROOT)
    collection_name = None
    lock = threading.Lock()
    use_for_related_fields = True

    def fetch_all(self):
        with self.lock:
            response, content = self.client.request(self.url, headers={'Accept': 'application/json'})

        if response.status == 200 and not response.fromcache:
            data = json.loads(content)
            # Remove obsolete records
            self.only('href').exclude(href__in=[item['href'] for item in data[self.collection_name]]).delete()
            self._handle_response(data)
        return self.all()

    def _handle_response(self, response):
        raise NotImplementedError

    @property
    def url(self):
        raise NotImplementedError


class RemoteMixin(object):
    lock = threading.Lock()
    http_client = httplib2.Http(app_settings.CACHE_ROOT)

    @classmethod
    def query(cls, path):
        url = urlparse.urljoin(app_settings.STORAGE_URL, path)
        cls.lock.acquire()
        response = cls.http_client.request(url, headers={'Accept': 'application/json'})
        cls.lock.release()
        return response


class CategoryManager(models.Manager, RemoteMixin):
    def fetch_all(self):
        response, content = self.query('categories/')

        if response.status == 200 and not response.fromcache:
            data = json.loads(content)
            # Remove obsolete categories
            self.get_queryset().only('href').exclude(href__in=[category['href']
                                                               for category in data['categories']]).delete()
            # Update existing or insert new categories
            for category in data['categories']:
                self.model(href=category['href'], name=category['name'], slug=category['slug'],
                           parent=category['parent'] and self.get(href=category['parent'])).save()

        return self.all()


class TagManager(models.Manager, RemoteMixin):
    def fetch_all(self):
        response, content = self.query('tags/')

        if response.status == 200 and not response.fromcache:
            data = json.loads(content)
            # Remove obsolete tags
            self.get_queryset().only('href').exclude(
                href__in=[tag['href'] for tag in data['tags']]).delete()
            # Update existing or insert new tags
            for tag in data['tags']:
                self.model(href=tag['href'], name=tag['name']).save()

        return self.all()


class FormatManager(models.Manager, RemoteMixin):
    def fetch_all(self):
        response, content = self.query('formats/')

        if response.status == 200 and not response.fromcache:
            data = json.loads(content)
            # Remove obsolete formats
            self.get_queryset().only('href').exclude(
                href__in=[format['href'] for format in data['formats']]).delete()
            # Update existing or insert new formats
            for format in data['formats']:
                self.model(**format).save()

        return self.all()


class DatasetManager(RemoteManager):
    collection_name = 'datasets'
    _url = None

    def _handle_response(self, response):
        # Update existing or insert new datasets
        categories = {}
        tags = {}
        for dataset in response[self.collection_name]:
            queryset = self.filter(href=dataset['href'])
            if queryset.exists():
                obj = queryset.get()
                obj.slug = dataset['slug']
                obj.name = dataset['name']
                obj.num_files = dataset['files']
            else:
                obj = self.model(href=dataset['href'], name=dataset['name'], slug=dataset['slug'],
                                 num_files=dataset['files'])
            obj.save()
            for category in dataset['categories']:
                if category['href'] not in categories:
                    categories[category['href']], _ = Category.objects.get_or_create(
                        href=category['href'],
                        defaults={'name': category['name'], 'slug': category['slug'], 'parent': category['parent']})
                obj.categories.add(categories[category['href']])

            for tag in dataset['tags']:
                if tag['href'] not in tags:
                    tags[tag['href']], _ = Tag.objects.get_or_create(href=tag['href'], defaults={'name': tag['name']})
                obj.tags.add(tags[tag['href']])

    @property
    def url(self):
        if self._url is None:
            self._url = urlparse.urljoin(app_settings.STORAGE_URL, 'datasets/')
        return self._url


class FileManager(RemoteManager):
    collection_name = 'files'
    _url = None

    def _handle_response(self, response):
        Dataset.objects.fetch_all()

        # Update existing or insert new files
        datasets = {}
        formats = {}
        tags = {}
        for file_ in response[self.collection_name]:
            if file_['dataset'] not in datasets:
                datasets[file_['dataset']] = Dataset.objects.get(href=file_['dataset'])
            if file_['default_format'] not in formats:
                formats[file_['default_format']] = Format.objects.get(href=file_['default_format'])
            obj = self.model(href=file_['href'], name=file_['name'], default_format=formats[file_['default_format']],
                             num_revisions=file_['revisions'], dataset=datasets[file_['dataset']])
            obj.save()

            for tag in file_['tags']:
                if tag['href'] not in tags:
                    tags[tag['href']], _ = Tag.objects.get_or_create(href=tag['href'], defaults={'name': tag['name']})
                obj.tags.add(tags[tag['href']])

    @property
    def url(self):
        if self._url is None:
            self._url = urlparse.urljoin(app_settings.STORAGE_URL, 'files/')
        return self._url


class RevisionManager(models.Manager, RemoteMixin):
    use_for_related_fields = True

    def fetch_all(self):
        response, content = self.query('revisions/')

        if response.status == 200 and not response.fromcache:
            File.objects.fetch_all()

            data = json.loads(content)
            # Remove obsolete revisions
            self.get_queryset().only('href').exclude(href__in=[r['href']
                                                               for r in data['revisions']]).delete()
            # Update existing or insert new revisions
            files = {}
            tags = {}
            formats = {}
            for r in data['revisions']:
                if r['format'] not in formats:
                    formats[r['format']] = Format.objects.get(href=r['format'])
                if r['file'] not in files:
                    files[r['file']] = File.objects.get(href=r['file'])

                o = self.model(href=r['href'], level=r['revision'], format=formats[r['format']], size=r['size'],
                               file=files[r['file']], updated_at=r['updated_at'])
                o.save()

                for t in r['tags']:
                    if t['href'] not in tags:
                        tags[t['href']], x = Tag.objects.get_or_create(href=t['href'], defaults={'name': t['name']})
                    o.tags.add(tags[t['href']])

        return self.all()


class Category(models.Model, RemoteMixin):
    """Represents categories used to organise datasets."""
    objects = CategoryManager()

    href = models.URLField(primary_key=True, editable=False)
    """The API path used to retrieve further details for this category."""
    name = models.CharField(max_length=50, blank=False)
    """The name of this category."""
    slug = models.SlugField(unique=True)
    """A unique keyword identifier for this category."""
    parent = models.ForeignKey('self', null=True, blank=True, related_name='subcategories', related_query_name='subcategory')
    """The parent of this instance in the category hierarchy, or None if it is a top-level category."""

    def __str__(self):
        """Return the name of this category."""
        return self.name

    def get_absolute_url(self):
        """Return a URL that can be used to obtain more details about this dataset."""
        return reverse('bdr.frontend:category-detail', kwargs={'slug': self.slug})

    class Meta(object):
        """Metadata options for the Category model class."""
        ordering = ['name']
        """Order results lexicographically by name."""
        unique_together = (('name', 'parent'),)
        """Require that no two sibling categories have the same name."""


class Tag(models.Model, RemoteMixin):
    """Represents tags used to annotate datasets, files and revisions."""
    objects = TagManager()

    href = models.URLField(primary_key=True, editable=False)
    """The API path used to retrieve further details for this tag."""
    name = models.CharField(unique=True, max_length=25)
    """The name of this tag."""

    def __str__(self):
        """Return the name of this tag prefixed by a hash symbol (e.g. #test)."""
        return '#{!s}'.format(self.name)


class Dataset(models.Model, RemoteMixin):
    """
    Represents datasets maintained by this repository.

    This class overrides the get_absolute_url method of the Django Model class.
    """
    objects = DatasetManager()

    href = models.URLField(primary_key=True, editable=False)
    """The API path used to retrieve further details about this dataset."""
    name = models.CharField(max_length=100, unique=True, blank=False)
    """The name of this dataset."""
    slug = models.SlugField(unique=True, blank=False, db_index=True,
                            error_messages={'unique': 'A dataset with this identifier already exists.'},
                            help_text='A unique, keyword identifier containing letters, numbers and dashes.')
    """A unique, keyword identifier for this dataset."""
    num_files = models.PositiveSmallIntegerField(editable=False, default=0)
    """The number of files associated with this dataset."""
    notes = models.TextField(blank=True)
    """Custom notes and annotations for this dataset."""
    update_uri = models.URLField(blank=True)
    """A URL specifying the update source for files in this dataset."""
    update_username = models.CharField(max_length=50, blank=True)
    """An optional user name for authenticating with the update source."""
    update_password = models.CharField(max_length=64, blank=True)
    """An optional password for authenticating with the update source."""
    update_frequency = models.PositiveIntegerField(default=0)
    """How often (in hours) this dataset should be updated; updates are not conducted if zero (0)."""
    updated_at = models.DateTimeField(null=True, editable=False)
    """Records the last update time for this dataset."""
    categories = models.ManyToManyField(Category, blank=True, related_name='datasets', related_query_name='dataset')
    """The categories assigned to this dataset."""
    tags = models.ManyToManyField(Tag, blank=True, related_name='datasets', related_query_name='dataset')
    """The tags used to annotate this dataset."""

    def fetch(self):
        response, content = self.query(self.href)

        if response.status == 200 and not response.fromcache:
            Format.objects.fetch_all()
            data = json.loads(content)

            self.href = data['href']
            self.name = data['name']
            self.slug = data['slug']
            self.num_files = len(data['files'])
            self.notes = data['notes']
            self.update_uri = data['update_uri']
            self.update_username = data['update_username']
            self.update_password = data['update_password']
            self.update_frequency = data['update_frequency']
            self.updated_at = data['updated_at']
            self.save()

            File.objects.only('href').filter(dataset=self).exclude(
                href__in=[f['href'] for f in data['files']]).delete()

            formats = {}
            for f in data['files']:
                if f['default_format'] not in formats:
                    formats[f['default_format']] = Format.objects.get(href=f['default_format']).fetch()
                ref = File(href=f['href'], name=f['name'], dataset=self, default_format=formats[f['default_format']],
                           num_revisions=f['revisions'])
                ref.save()
                for tag in f['tags']:
                    t, new = Tag.objects.get_or_create(href=tag['href'], defaults={'name': tag['name']})
                    ref.tags.add(t)
        return self

    def get_absolute_url(self):
        """Return a URL that can be used to obtain more details about this dataset."""
        return reverse('bdr.frontend:dataset-detail', kwargs={'slug': self.slug})

    class Meta(object):
        """Metadata options for the Dataset model class."""
        ordering = ['name']
        """Order results lexicographically by name."""


class File(models.Model, RemoteMixin):
    objects = FileManager()

    href = models.URLField(primary_key=True, editable=False)
    """The API path used to retrieve further details about this file."""
    name = models.CharField(max_length=100, unique=True, blank=False)
    """The name of this file."""
    default_format = models.ForeignKey('Format', related_name='files', related_query_name='file')
    """The format applied to all new revisions."""
    dataset = models.ForeignKey(Dataset, related_name='files', related_query_name='file')
    """The dataset to which this file belongs."""
    num_revisions = models.PositiveSmallIntegerField(default=0, editable=False)
    """The number of revisions associated with this file."""
    tags = models.ManyToManyField(Tag, blank=True, related_name='files', related_query_name='file')
    """The tags used to annotate this file."""

    def fetch(self):
        response, content = self.query(self.href)

        if response.status == 200 and not response.fromcache:
            Format.objects.fetch_all()
            data = json.loads(content)

            f = File(href=data['href'], name=data['name'], num_revisions=len(data['revisions']), dataset=self.dataset,
                     default_format=Format.objects.get(href=data['default_format']))
            f.save()

            formats = {}
            for revision in data['revisions']:
                if revision['format'] not in formats:
                    formats[revision['format']] = Format.objects.get(href=revision['format']).fetch()
                ref = Revision(href=revision['href'], file=f, level=revision['revision'],
                               format=formats[revision['format']], size=revision['size'],
                               updated_at=revision['updated_at'])
                ref.save()

                for tag in revision['tags']:
                    t, new = Tag.objects.get_or_create(href=tag['href'], defaults={'name': tag['name']})
                    ref.tags.add(t)

        return self

    def get_absolute_url(self):
        """Return a URL that can be used to obtain more details about this file."""
        return reverse('bdr.frontend:file-detail', kwargs={'ds': self.dataset.slug, 'fn': self.name})


class Format(models.Model, RemoteMixin):
    """
    Represents the format for files maintained by this repository.

    This class overrides the get_absolute_url method of the Django Model class.
    """
    objects = FormatManager()

    MODULE_NAME = 'bdr.backend.formats.simple'

    href = models.URLField(primary_key=True, editable=False)
    """The API path used to retrieve further details about this format."""
    name = models.CharField(max_length=50, unique=True, blank=False)
    """The name of this format."""
    slug = models.SlugField(unique=True, blank=False, db_index=True,
                            error_messages={'unique': 'A format with this identifier already exists.'},
                            help_text='A unique, keyword identifier containing letters, numbers and dashes.')
    """A unique, keyword identifier for this format."""
    separator = models.CharField(max_length=1)
    """The separating character between fields."""
    comment = models.CharField(max_length=1, blank=True)
    """A character that denotes that a line is a comment."""
    quote = models.CharField(max_length=1, blank=True)
    """The character that can be used to wrap strings with special characters."""
    module = models.CharField(max_length=100, default=MODULE_NAME)
    """The name of the module that can be used to read and write files of this format."""

    def fetch(self):
        response, content = self.query(self.href)

        if response.status == 200 and not response.fromcache:
            data = json.loads(content)

            self.href = data['href']
            self.name = data['name']
            self.slug = data['slug']
            self.separator = data['separator']
            self.comment = data['comment']
            self.quote = data['quote']
            self.module = data['module']

            FormatField.objects.filter(format=self).delete()
            for field in data['fields']:
                instance, _ = FormatField.objects.get_or_create(format=self, name=field['name'],
                                                                ordinal=field['ordinal'],
                                                                defaults={'is_key': field['is_key']})
                self.fields.add(instance)
            self.save()
        return self

    @property
    def can_edit(self):
        return self.module == self.MODULE_NAME

    def get_absolute_url(self):
        """Return a URL that can be used to obtain more details about this dataset."""
        return reverse('bdr.frontend:format-detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name

    class Meta(object):
        """Metadata options for the Dataset model class."""
        ordering = ['name']
        """Order results lexicographically by name."""


class FormatField(models.Model, RemoteMixin):
    """Represents a field within a file format."""
    format = models.ForeignKey(Format, related_name='fields', related_query_name='field')
    """The format in which this field is used."""
    name = models.CharField(max_length=50)
    """The name of this field."""
    ordinal = models.PositiveSmallIntegerField()
    """The order of this field within the format."""
    is_key = models.BooleanField()
    """Specifies whether this field is a record key."""

    class Meta(object):
        """Metadata options for the FormatField model class."""
        ordering = ['ordinal']
        """Order results by ordinal."""
        unique_together = (('format', 'name'), ('format', 'ordinal'))
        """Require that field names and ordinals are unique within a given format."""


class Revision(models.Model, RemoteMixin):
    """
    Represents revisions of files maintained by this repository.

    This class overrides the get_absolute_url method of the Django Model class.
    """
    objects = RevisionManager()

    href = models.URLField(primary_key=True, editable=False)
    """The API path used to retrieve further details about this revision."""
    level = models.PositiveIntegerField(editable=False)
    """The revision number of this revision."""
    file = models.ForeignKey(File, related_name='revisions', related_query_name='revision')
    """The file of which this revision is a part."""
    format = models.ForeignKey(Format, related_name='revisions', related_query_name='revision')
    """The format for this revision."""
    size = models.PositiveIntegerField(editable=False)
    """The file size of this revision."""
    updated_at = models.DateTimeField(null=True, editable=False)
    """The modification date and time for this revision."""
    tags = models.ManyToManyField(Tag, blank=True, related_name='revisions', related_query_name='revision')
    """The tags used to annotate this revision."""

    def get_absolute_url(self):
        """Return a URL that can be used to download this revision."""
        return reverse('bdr.frontend:download',
                       kwargs={'ds': self.file.dataset.slug, 'fn': self.file.name, 'rev': self.level})

    class Meta(object):
        """Metadata options for the Revision model class."""
        ordering = ['-level']
        """Place results in descending order of revision number."""
        unique_together = (('file', 'level'),)
        """Require that each revision number is unique for revisions of any given file."""
