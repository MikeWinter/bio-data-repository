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

from django.core.urlresolvers import reverse
from django.db import models
from hashlib import md5 as hash_algorithm
import io
import os.path
import shutil
import tempfile
import xdelta

from .. import app_settings


class Category(models.Model):
    """
    Represents categories used to organise datasets.

    This class overrides the get_absolute_url method of the Django Model class.
    """
    name = models.CharField(max_length=50, blank=False)
    """The name of this category."""
    slug = models.SlugField(unique=True)
    """A unique keyword identifier for this category."""
    parent = models.ForeignKey('self', null=True, blank=True, related_name='subcategories',
                               related_query_name='subcategory')
    """The parent of this instance in the category hierarchy, or None if it is a top-level category."""

    def __str__(self):
        """Return the name of this category."""
        return str(self.name)

    def get_absolute_url(self):
        """Return a URL that can be used to obtain more details about this category."""
        return reverse('bdr.backend:category-detail', kwargs={'slug': self.slug})

    class Meta(object):
        """Metadata options for the Category model class."""
        ordering = ['name']
        """Order results lexicographically by name."""
        unique_together = (('name', 'parent'),)
        """Require that no two sibling categories have the same name."""


class Tag(models.Model):
    """
    Represents tags used to annotate datasets, files and revisions.

    This class overrides the get_absolute_url method of the Django Model class.
    """
    name = models.CharField(max_length=25, unique=True, blank=False)
    """The name of this tag."""

    def get_absolute_url(self):
        """Return a URL that can be used to obtain more details about this tag."""
        return reverse('bdr.backend:tag-detail', kwargs={'pk': self.pk})

    class Meta(object):
        """Metadata options for the Tag model class."""
        ordering = ['name']


class Format(models.Model):
    """
    Represents the format of files stored in the repository.

    This class overrides the get_absolute_url method of the Django Model class.
    """
    name = models.CharField(max_length=50, unique=True, blank=False)
    """The name of the format."""
    slug = models.SlugField(unique=True)
    """A unique keyword identifier for this format."""
    separator = models.CharField(max_length=1)
    """The separating character between fields."""
    comment = models.CharField(max_length=1, blank=True)
    """The character used to delimit comments."""
    quote = models.CharField(max_length=1, blank=True)
    """The character that can be used to wrap strings with special characters."""
    module = models.CharField(max_length=100)
    """The name of the module that can be used to read and write files of this format."""

    def get_absolute_url(self):
        """Return a URL that can be used to obtain more details about this format."""
        return reverse('bdr.backend:format-detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name


class FormatField(models.Model):
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


class Dataset(models.Model):
    """
    Represents datasets (collections of related files) maintained by this repository.

    This class overrides the get_absolute_url method of the Django Model class.
    """
    name = models.CharField(max_length=100, unique=True, blank=False)
    """The name of this dataset."""
    slug = models.SlugField(unique=True, blank=False, db_index=True)
    """A unique, keyword identifier for this dataset."""
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
    update_size = models.PositiveIntegerField(default=0, editable=False)
    """The size of the resource last used to automatically update the dataset."""
    updated_at = models.DateTimeField(null=True)
    """Records the last update time for this dataset."""
    checked_at = models.DateTimeField(null=True, blank=True)
    """Records the last time this dataset was checked for updates."""
    categories = models.ManyToManyField(Category, blank=True, related_name='datasets', related_query_name='dataset')
    """The categories assigned to this dataset."""
    tags = models.ManyToManyField(Tag, blank=True, related_name='datasets', related_query_name='dataset')
    """The tags used to annotate this dataset."""

    def delete(self, using=None):
        path = self.get_storage_path()
        if os.path.exists(path):
            shutil.rmtree(path)
        super(Dataset, self).delete(using=using)

    def get_absolute_url(self):
        """Return a URL that can be used to obtain more details about this dataset."""
        return reverse('bdr.backend:dataset-detail', kwargs={'slug': self.slug})

    def get_storage_path(self):
        return os.path.join(app_settings.STORAGE_ROOT, self.slug)

    def __str__(self):
        return str(self.name)

    class Meta(object):
        """Metadata options for the Dataset model class."""
        ordering = ['name']
        """Order results lexicographically by name."""


class Source(models.Model):
    """
    Represents a remote location that can be used to update one or more files within a dataset.
    """
    url = models.URLField(blank=True)
    """A URL specifying the update source for files in this dataset."""
    dataset = models.ForeignKey(Dataset, related_name='datasets', related_query_name='dataset')
    """The dataset to which this update source relates."""
    username = models.CharField(max_length=50, blank=True)
    """An optional user name for authentication."""
    password = models.CharField(max_length=64, blank=True)
    """An optional password for authentication."""
    frequency = models.PositiveIntegerField(default=0)
    """How often (in hours) this source should be checked for updates; skipped if zero (0)."""
    checked_at = models.DateTimeField(null=True, blank=True)
    """Records the last time this source was checked for updates."""

    class Meta(object):
        unique_together = (('url', 'dataset'),)
        """Require that datasets do not have duplicate source locations."""


class File(models.Model):
    """
    Represents the files that constitute each dataset maintained by this repository.

    This class overrides the get_absolute_url method of the Django Model class.
    """
    name = models.CharField(max_length=100, blank=False, db_index=True)
    """The name of this file."""
    dataset = models.ForeignKey(Dataset, related_name='files', related_query_name='file')
    """The dataset to which this file belongs."""
    default_format = models.ForeignKey(Format, related_name='files', related_query_name='file')
    """The format of this file."""
    tags = models.ManyToManyField(Tag, blank=True, related_name='files', related_query_name='file')
    """The tags used to annotate this file."""

    def delete(self, using=None):
        for revision in self.revisions.order_by('level'):
            revision.delete(using=using)
        super(File, self).delete(using=using)

    def get_absolute_url(self):
        """Return a URL that can be used to obtain more details about this file."""
        return reverse('bdr.backend:file-detail', kwargs={'ds': self.dataset.slug, 'fn': self.name})

    def __str__(self):
        return str(self.name)

    class Meta(object):
        """Metadata options for the File model class."""
        ordering = ['name']
        """Place results in ascending order by name."""
        unique_together = (('name', 'dataset'),)
        """Require that file names are unique within a given dataset."""


class Revision(models.Model):
    def __init__(self, *args, **kwargs):
        self._data = None
        super(Revision, self).__init__(*args, **kwargs)

    """
    Represents revisions of files maintained by this repository.

    This class overrides the get_absolute_url method of the Django Model class.
    """
    @staticmethod
    def _get_path(instance, filename):
        """
        Compute the path name for a revision based on the dataset identifier, file name and revision level.

        :param instance: An instance of the model.
        :type instance:  Revision
        :type filename:  str
        :return: The path name for a revision.
        :rtype:  str
        """
        base = hash_algorithm(instance.file.name).hexdigest()
        name = "{0}.{1}.diff".format(base, instance.level)
        return os.path.join("", [instance.file.dataset.slug, name])

    file = models.ForeignKey(File, related_name='revisions', related_query_name='revision')
    """The file of which this revision is a part."""
    level = models.PositiveIntegerField(editable=False)
    """The revision number of this revision."""
    size = models.PositiveIntegerField(editable=False)
    """The file size of this revision."""
    format = models.ForeignKey(Format, related_name='revisions', related_query_name='revision')
    """The format of this file."""
    updated_at = models.DateTimeField(editable=False)
    """The modification date and time for this revision."""
    tags = models.ManyToManyField(Tag, blank=True, related_name='revisions', related_query_name='revision')
    """The tags used to annotate this revision."""

    @property
    def data(self):
        if self._data is None:
            path = self._get_pathname()
            if not os.path.exists(path):
                raise Exception
            file_ = io.open(path, 'rb')
            self._data = xdelta.DeltaFile(file_)
            self._data.source = self._decode_chain(self.get_previous())
        self._data.open('rb')
        return self._data

    @data.setter
    def data(self, file_):
        # TODO: get_next()/get_previous() are reversed: the next revision should be the next higher revision number and
        # TODO: it is this which is the source while writing. These methods need to be fixed and the uses below swapped.
        # TODO: However, current use elsewhere needs to be changed, too.
        # Decode the revision that precedes this one in the chain
        next_revision = self.get_previous()
        next_data = self._decode_chain(next_revision)

        # Decode previous revision using current data
        previous_revision = self.get_next()
        if os.path.exists(self._get_pathname()):
            chain_start = (next_data, next_revision)
        else:
            # If this revision has no data file, the previous revision is standalone
            chain_start = (None, previous_revision)
        previous_data = self._decode_chain(previous_revision, chain_start)

        if self._data is None:
            self._data = self._create_file_object()
            self._data.source = next_data
        self._data.open('wb')

        source = self._make_seekable(file_)
        # Encode new data
        with self._data as stream:
            while True:
                chunk = source.read(io.DEFAULT_BUFFER_SIZE)
                if not chunk:
                    break
                stream.write(chunk)
            source.seek(0)

        # Recode previous revision
        if previous_data:
            with previous_revision._create_file_object() as delta:
                delta.source = source
                delta.open('wb')
                while True:
                    chunk = previous_data.read(io.DEFAULT_BUFFER_SIZE)
                    if not chunk:
                        break
                    delta.write(chunk)

    def get_absolute_url(self):
        """Return a URL that can be used to obtain more details about this revision."""
        return reverse('bdr.backend:revision-detail',
                       kwargs={'ds': self.file.dataset.slug, 'fn': self.file.name, 'rev': self.level})

    def get_next(self):
        return type(self).objects.filter(file=self.file, level__lt=self.level).first()

    def get_previous(self):
        return type(self).objects.filter(file=self.file, level__gt=self.level).last()

    @classmethod
    def _decode_chain(cls, to, from_=None):
        if not to:
            return None

        revisions = cls.objects.filter(file=to.file).order_by('level')
        if from_ is None:
            from_ = None, revisions.last()
        file_, revision = from_

        for current in revisions.filter(level__range=(revision.level, to.level)).reverse():
            with xdelta.DeltaFile(io.open(current._get_pathname(), 'rb')) as source:
                source.source = file_
                target = tempfile.TemporaryFile()
                for chunk in source.chunks():
                    target.write(chunk)
            file_ = target
            file_.seek(0)
        return file_

    @classmethod
    def _make_seekable(cls, file_):
        if hasattr(file_, 'seekable') and file_.seekable():
            return file_

        temp = tempfile.TemporaryFile()
        while True:
            chunk = file_.read(io.DEFAULT_BUFFER_SIZE)
            if not chunk:
                break
            temp.write(chunk)
        temp.flush()
        temp.seek(0)
        return temp

    def _create_file_object(self):
        path = self._get_pathname()
        parent = os.path.dirname(path)
        if not os.path.exists(parent):
            os.makedirs(parent, app_settings.STORAGE_MODE)

        file_ = io.open(path, 'wb')
        delta = xdelta.DeltaFile(file_)
        return delta

    def _get_pathname(self):
        from hashlib import sha224 as hash_algorithm
        filename = '{:s}.{:05x}.diff'.format(hash_algorithm(self.file.name).hexdigest(), self.level)
        return os.path.join(app_settings.STORAGE_ROOT, self.file.dataset.slug, filename)

    class Meta(object):
        """Metadata options for the Revision model class."""
        ordering = ['-level']
        """Place results in descending order of revision number."""
        unique_together = (('file', 'level'),)
        """Require that each revision number is unique for revisions of any given file."""
