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

import os.path
import shutil

from django.core.urlresolvers import reverse
from django.db import models

from . import app_settings


class Category(models.Model):
    """
    Represents categories used to organise datasets.

    This class overrides the get_absolute_url method of the Django Model class.
    """
    name = models.CharField(max_length=50, blank=False)
    """The name of this category."""
    slug = models.SlugField(unique=True)
    """A unique keyword identifier for this category."""
    parent = models.ForeignKey('self', null=True, blank=True, related_name='subcategories', related_query_name='subcategory')
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
    STRING = 1
    INTEGER = 2
    DECIMAL = 3
    BOOLEAN = 4

    _TYPE_CHOICES = (
        (STRING, 'string'),
        (INTEGER, 'integer'),
        (DECIMAL, 'decimal'),
        (BOOLEAN, 'boolean'),
    )

    format = models.ForeignKey(Format, related_name='fields', related_query_name='field')
    """The format in which this field is used."""
    name = models.CharField(max_length=50)
    """The name of this field."""
    ordinal = models.PositiveSmallIntegerField()
    """The order of this field within the format."""
    is_key = models.BooleanField()
    """Specifies whether this field is a record key."""
    type = models.PositiveSmallIntegerField(choices=_TYPE_CHOICES, default=STRING)
    """The type of this field."""

    class Meta(object):
        """Metadata options for the FormatField model class."""
        ordering = ['ordinal']
        """Order results by ordinal."""
        unique_together = (('format', 'name'), ('format', 'ordinal'))
        """Require that field names and ordinals are unique within a given format."""


class Dataset(models.Model):
    """
    Represents datasets maintained by this repository.

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
        slug = self.slug
        super(Dataset, self).delete(using=using)
        path = os.path.join(app_settings.STORAGE_ROOT, slug)
        shutil.rmtree(path, ignore_errors=True)

    def get_absolute_url(self):
        """Return a URL that can be used to obtain more details about this dataset."""
        return reverse('bdr.backend:dataset-detail', kwargs={'slug': self.slug})

    def __str__(self):
        return str(self.name)

    class Meta(object):
        """Metadata options for the Dataset model class."""
        ordering = ['name']
        """Order results lexicographically by name."""


class File(models.Model):
    """
    Represents files maintained by this repository.

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
    """
    Represents revisions of files maintained by this repository.

    This class overrides the get_absolute_url method of the Django Model class.
    """
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

    def get_absolute_url(self):
        """Return a URL that can be used to obtain more details about this revision."""
        return reverse('bdr.backend:revision-detail',
                       kwargs={'ds': self.file.dataset.slug, 'fn': self.file.name, 'rev': self.level})

    def get_next(self):
        return self._default_manager.filter(file=self.file, level__lt=self.level).first()

    def get_previous(self):
        return self._default_manager.filter(file=self.file, level__gt=self.level).last()

    class Meta(object):
        """Metadata options for the Revision model class."""
        ordering = ['-level']
        """Place results in descending order of revision number."""
        unique_together = (('file', 'level'),)
        """Require that each revision number is unique for revisions of any given file."""
