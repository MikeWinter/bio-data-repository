"""
This module contains class definitions for the domain model of this
application.

The classes exported by this module include:

    Category
        Groups datasets into a hierarchical structure.
    Dataset
        A collection of data files maintained by the repository.
    File
        Represents the files that constitute each dataset.
    Filter
        Analyses (and optionally transforms) the names of files retrieved from
        data sources.
    Revision
        Represents revisions of files maintained by this repository.
    Source
        Represents a remote location that can be used to update one or more
        files within a dataset.
    Tag
        Annotate datasets, data files and revisions.
    Update
        Records updates made to the repository for each dataset.
"""

from datetime import datetime, timedelta
from urlparse import urlsplit
import re

from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.db.models import Model, fields, SET_DEFAULT
from django.db.models.fields import files, related
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import importlib
from django.utils.text import slugify

from .formats import get_entry_point
from .utils import utc, RemoteFile
from .utils.archives import Archive
from .utils.storage import delta_storage, upload_path
from .utils.transports import Transport

__all__ = ["Category", "Dataset", "File", "Filter", "Revision", "Source", "Tag", "Update"]
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


_BACK_REFERENCE = re.compile(r"\\(\d{1,2})")
r"""
Matches back-references used in regular expression substitutions (e.g. \1).
"""


def _validate_regex(value):
    try:
        re.compile(value)
    except re.error as error:
        raise ValidationError("Invalid pattern: {0:s}".format(error))


class Category(Model):
    """
    Categories organise datasets into a hierarchical structure.

    The datasets belonging to a category can be retrieved using the
    :py:attr:`datasets` property of an instance.

    This class overrides the :py:meth:`~Model.get_absolute_url` method of the
    :py:class:`Model` class.
    """

    name = fields.CharField(max_length=50, unique=True)
    """The name of this category."""

    def get_absolute_url(self):
        """
        Return a URL that can be used to obtain more details about this
        category.
        """
        return reverse("bdr:view-category", kwargs={"pk": self.pk,
                                                    "name": slugify(unicode(self.name))})

    def __unicode__(self):
        return self.name

    class Meta(object):
        """Metadata options for the ``Category`` model class."""

        ordering = ["name"]
        verbose_name_plural = "categories"


class Tag(Model):
    """
    Tags annotate datasets, data files and revisions.

    The entities associated with a given tag can be retrieved via their
    respective properties :py:attr:`datasets`, :py:attr:`datafiles` and
    :py:attr:`revisions`.

    This class overrides the :py:meth:`~Model.get_absolute_url` method of the
    :py:class:`Model` class.
    """

    name = fields.CharField(max_length=25, unique=True)
    """The name of this tag."""

    def get_absolute_url(self):
        """
        Return a URL that can be used to obtain more details about this tag.
        """
        return reverse("bdr:view-tag", kwargs={"pk": self.pk, "name": slugify(unicode(self.name))})

    @classmethod
    def get_field_names(cls):
        """
        Return the names of the fields in this model.

        :return: A list of field names belonging to this model.
        :rtype: list of unicode
        """
        return [field.name for field in cls._meta.concrete_fields]

    def __unicode__(self):
        return self.name

    class Meta(object):
        """Metadata options for the ``Tag`` model class."""

        ordering = ["name"]


class Format(Model):
    """
    Represents the format of files stored in the repository.

    This class overrides the :py:meth:`~Model.get_absolute_url` method of the
    :py:class:`Model` class.
    """

    name = fields.CharField(max_length=50, unique=True, blank=False)
    """The name of the format."""
    entry_point_name = fields.CharField(max_length=150, editable=False)
    """
    The name of the plugin that provides the functionality related to this
    format.
    """
    metadata = fields.BinaryField(blank=True)
    """Parser-specific information for this format."""

    @property
    def deletable(self):
        return "delete" in self.views

    @property
    def editable(self):
        return "edit" in self.views

    @property
    def realisable(self):
        return "create" in self.views

    @property
    def views(self):
        return get_entry_point(self.entry_point_name).views

    def reader(self, stream):
        """
        Return a :py:class:`Reader` over the given stream using this format.

        :param stream: A readable data stream.
        :type stream: io.IOBase
        :return: A suitable ``Reader`` instance.
        :rtype: bdr.formats.Reader
        :raise ImportError: if this format does not have an associated Reader
                            class.
        """
        return self._get_type("Reader")(stream, self.metadata)

    def writer(self, stream, field_names):
        """
        Return a :py:class:`Writer` over the given stream using this format.

        :param stream: A writable data stream.
        :type stream: io.IOBase
        :param field_names: An iterable that contains the names of fields to be
                            written to ``stream``.
        :type field_names: list of str | tuple of str
        :return: A suitable ``Writer`` instance.
        :rtype: bdr.formats.Writer
        :raise ImportError: if this format does not have an associated Writer
                            class.
        """
        return self._get_type("Writer")(stream, self.metadata, field_names)

    def get_absolute_url(self):
        """
        Return a URL that can be used to obtain more details about this format.
        """
        return reverse("bdr:view-format", kwargs={"pk": self.pk})

    def _get_type(self, class_name):
        module = importlib.import_module(self.module)
        type_object = getattr(module, class_name)
        if not type_object:
            raise ImportError("Appropriate module cannot be found (:s).".format(self.module))
        return type_object

    def __unicode__(self):
        return self.name

    class Meta(object):
        """Metadata options for the ``Format`` model class."""

        ordering = ["name"]


class Dataset(Model):
    """
    A dataset is collection of data files maintained by the repository.

    The contents of a dataset can be updated automatically from a remote source
    if one has been specified.

    This class overrides the :py:meth:`~Model.get_absolute_url` method of the
    :py:class:`Model` class.
    """

    name = fields.CharField(max_length=100)
    """The name of this dataset."""
    notes = fields.TextField(blank=True)
    """Custom notes and annotations for this dataset."""
    categories = related.ManyToManyField(Category, blank=True, related_name="datasets",
                                         related_query_name="dataset")
    """The categories assigned to this dataset."""
    tags = related.ManyToManyField(Tag, blank=True, related_name="datasets",
                                   related_query_name="dataset")
    """The tags used to annotate this dataset."""

    def update(self):
        """
        Query the sources for this dataset and add revisions for any modified
        files.
        """
        for source in [src for src in self.sources.all() if src.has_update_elapsed()]:
            source.checked()

            if source.has_changed():
                file_list, size, modification_date = source.files()
                update = self.updates.create(source=source, size=size,
                                             modified_at=modification_date)
                for source_file in file_list:
                    self.add_file(source_file, update)

    # noinspection PyShadowingBuiltins
    def add_file(self, file, update, format=None):
        """
        Add the given file to this dataset and associate it with ``update``.

        If the file does not already exist, it will be created. The file name
        is taken from the name property of the file.

        :param file: The file to add.
        :type file: django.core.files.File
        :param update: The update with which this addition should be
                       associated.
        :type update: Update
        :param format: (Optional) The default format for revisions of this
                       file.
        :type format: Format | None
        """
        file_defaults = {"default_format": format}
        instance = self.files.get_or_create(name=file.name, defaults=file_defaults)[0]
        instance.revisions.create(data=file, size=file.size, update=update)

    def get_absolute_url(self):
        """
        Return a URL that can be used to obtain more details about this
        dataset.
        """
        return reverse("bdr:view-dataset", kwargs={"dpk": self.pk,
                                                   "dataset": slugify(unicode(self.name))})

    @classmethod
    def get_field_names(cls):
        """
        Return the names of the fields in this model.

        :return: A list of field names belonging to this model.
        :rtype: list of unicode
        """
        return [field.name for field in cls._meta.concrete_fields]

    def __unicode__(self):
        return self.name

    class Meta(object):
        """Metadata options for the ``Dataset`` model class."""

        ordering = ["name"]
        """Order results lexicographically by name."""


class File(Model):
    """
    Represents the files that constitute each dataset maintained by this
    repository.

    This class overrides the :py:meth:`~Model.get_absolute_url` method of the
    :py:class:`Model` class.
    """

    name = fields.CharField(max_length=100, blank=False,
                            help_text='<span class="text-warning">Note: Any filters that map to'
                                      ' this file name must also be changed if the file is'
                                      ' renamed.</span>')
    """The name of this file."""
    dataset = related.ForeignKey(Dataset, editable=False, related_name="files",
                                 related_query_name="file")
    """The dataset to which this file belongs."""
    default_format = related.ForeignKey(Format, related_name="files", related_query_name="file",
                                        default=1, on_delete=SET_DEFAULT)
    """The default format for revision of this file."""
    tags = related.ManyToManyField(Tag, blank=True, related_name="files",
                                   related_query_name="file")
    """The tags used to annotate this file."""

    def get_absolute_url(self):
        """
        Return a URL that can be used to obtain more details about this file.
        """
        return reverse("bdr:view-file",
                       kwargs={"dpk": self.dataset.pk,
                               "dataset": slugify(unicode(self.dataset.name)),
                               "fpk": self.pk, "filename": slugify(unicode(self.name))})

    @classmethod
    def get_field_names(cls):
        """
        Return the names of the fields in this model.

        :return: A list of field names belonging to this model.
        :rtype: list of unicode
        """
        return [field.name for field in cls._meta.concrete_fields]

    def __unicode__(self):
        return self.name

    class Meta(object):
        """Metadata options for the File model class."""

        ordering = ["name"]
        """Place results in ascending order by name."""
        unique_together = (("dataset", "name"),)
        """Require that file names are unique within a given dataset."""


class Source(Model):
    """
    Represents a remote location that can be used to update one or more files
    within a dataset.

    This class overrides the :py:meth:`~Model.get_absolute_url` method of the
    :py:class:`Model` class.
    """

    url = fields.URLField(verbose_name="URL")
    """A URL specifying the update source for files in this dataset."""
    dataset = related.ForeignKey(Dataset, editable=False, related_name="sources",
                                 related_query_name="source")
    """The dataset to which this update source relates."""
    username = fields.CharField(max_length=50, blank=True)
    """An optional user name for authentication."""
    password = fields.CharField(max_length=64, blank=True)
    """An optional password for authentication."""
    period = fields.PositiveSmallIntegerField(default=0, verbose_name="Update period",
                                              help_text="The time, in hours, between update checks."
                                                        " If zero, automatic updates are disabled.")
    """
    The time, in hours, between updates using this source; skipped if zero (0).
    """
    checked_at = fields.DateTimeField(blank=True, null=True, editable=False)
    """The last time this source was checked for updates."""
    transport_provider_factory = Transport.instance
    """
    A callable that returns Transport instances. The factory must accept three
    parameters: url, user, and password.
    """
    archive_factory = Archive.instance
    """
    A callable that returns Archive instances. The factory must accept two
    parameters: archive_file and path.
    """

    def __init__(self, *args, **kwargs):
        super(Source, self).__init__(*args, **kwargs)
        self._provider = None

    def get_absolute_url(self):
        """
        Return a URL that can be used to obtain more details about this source.
        """
        return reverse("bdr:view-source", kwargs={"source": self.pk, "dpk": self.dataset.pk,
                                                  "dataset": slugify(unicode(self.dataset.name))})

    def files(self):
        """
        Fetch the files obtainable from this data source.

        The files returned will consist of only those that pass the filters
        applicable to this data source.

        :return: A filtered list of `RemoteFile` instances obtained from this
                 data source, the combined update size, and modification date.
        :rtype: tuple of (list of RemoteFile, long, datetime)
        """
        provider = self._get_transport_provider()
        archive = self._get_archive(provider.get_content())
        filters = self._get_filters()
        file_list = []
        for file_name in archive:  # type: str
            try:
                mapped_name = self._get_mapping(file_name, filters)
            except self.FileRejected:
                pass  # If a file is rejected, skip it.
            else:
                member = archive[file_name]
                new_file = RemoteFile(member.file, mapped_name, member.size, member.mtime)
                file_list.append(new_file)
        return file_list, provider.get_size(), provider.get_modification_date()

    def checked(self, timestamp=None):
        """
        Mark this source as checked.

        If the timestamp is omitted, the current time is used.

        :param timestamp: An optional timestamp denoting when this source was
                          checked.
        :type  timestamp: datetime | None
        """
        if timestamp is None:
            timestamp = datetime.now(utc)
        self.checked_at = timestamp
        self.save(update_fields=("checked_at",))

    def has_update_elapsed(self):
        """
        Return ``True` if this data source is due to be checked.

        If the update period is zero, this method returns ``False``.

        :return: ``True`` if this data source should be checked for updates;
                 ``False`` otherwise.
        :rtype:  bool
        """
        if not self.period:
            return False
        if not self.checked_at:
            return True
        delta = timedelta(hours=self.period)
        return self.checked_at + delta <= datetime.now(utc)

    def has_changed(self):
        """
        Determine whether the resource at this source has changed.

        :return: ``True`` if the resource has changed; otherwise ``False``.
        :rtype:  bool
        """
        changed = False
        try:
            latest_update = self.updates.latest()
        except self.updates.model.DoesNotExist:
            changed = True
        else:
            provider = self._get_transport_provider()
            if provider.get_size() != latest_update.size:
                changed = True
            else:
                updated_at = provider.get_modification_date()
                if (updated_at is None or latest_update.modified_at is None or
                        updated_at > latest_update.modified_at):
                    changed = True
        return changed

    @classmethod
    def _get_mapping(cls, file_name, filters):
        """
        Return the mapped name of a file based on the given filter list.

        :param file_name: The original file name.
        :type file_name: str
        :param filters: A list of filters to check the name against.
        :type filters: list of Filter
        :return: The mapped file name.
        :rtype: str
        :raises FileRejected: if the file is rejected by the filter list.
        """
        if not filters:
            return file_name
        for source_filter in filters:
            if source_filter.match(file_name):
                return source_filter.map(file_name)
        raise cls.FileRejected(file_name)

    def _get_archive(self, data):
        """
        Return an archive read from ``data``.

        :param data: A file-like object containing the data of an archive.
        :type data: file
        :return: The archive.
        :rtype: Archive
        """
        path = urlsplit(self.url).path
        return self.archive_factory(data, path)

    def _get_filters(self):
        """
        Return a list of filters (possibly empty) associated with this data
        source.

        :return: The list of filters.
        :rtype: list of Filter
        """
        return [self.filters.get(pk=pk) for pk in self.get_filter_order()]

    def _get_transport_provider(self):
        """
        Return a transport provider that can connect to this source.

        :return: The transport provider.
        :rtype: Transport
        """
        if self._provider is None:
            self._provider = self.transport_provider_factory(url=self.url, user=self.username,
                                                             password=self.password)
        return self._provider

    def __unicode__(self):
        return self.url

    class FileRejected(Exception):
        """Raised when a file is not matched by any filter."""

        pass

    class Meta(object):
        """Metadata options for the ``Source`` model class."""

        unique_together = (("dataset", "url"),)
        """Require that datasets do not have duplicate source locations."""


class Filter(Model):
    """
    Analyses (and optionally transforms) the names of files retrieved from data
    sources to determine whether they should be added to the dataset associated
    with that source.

    This class overrides the :py:meth:`~Model.get_absolute_url` method of the
    :py:class:`Model` class.
    """

    pattern = fields.CharField(max_length=100, verbose_name="Matching pattern",
                               validators=[_validate_regex])
    """
    A regular expression defining file names accepted by this filter. Capture
    groups can be referenced by the mapping specification.
    """
    inverted = fields.BooleanField(default=False)
    """
    If True, a file is accepted by this filter if the name does not match the
    pattern expression.
    """
    mapping = fields.CharField(max_length=100, blank=True, verbose_name="Replacement pattern")
    """
    A string which is used to replace the name of a matching data file. Part of
    the original name can be included by enclosing that part of the name in
    parentheses and referencing it in the mapping specification by prefixing
    the number of that group with a backslash.
    """
    source = related.ForeignKey(Source, editable=False, related_name="filters",
                                related_query_name="filter")
    """
    The data source filtered by this instance.
    """

    def map(self, filename):
        """
        Transform the given string according the replacement pattern.

        :param filename: The file name to transform.
        :type  filename: str
        :return: The transformed name.
        :rtype: str
        """
        if not self.mapping:
            return filename
        return re.sub(self.pattern, self.mapping, filename)

    def match(self, filename):
        """
        Test whether the specified file name matches the pattern required by
        this filter.

        :param filename: The file name to test.
        :type filename: str | unicode
        :return: True if the file name matches this filter; False otherwise.
        :rtype: bool
        """
        matches = re.search(self.pattern, filename) is not None
        return matches if not self.inverted else not matches

    def clean(self):
        """
        Validate this filter ensuring that the mapping, if specified, only
        references capture groups defined in the pattern expression.
        """
        if self.mapping:
            try:
                regex = re.compile(self.pattern)
            except re.error:
                # If compilation fails, don't bother validating the mapping
                # string.
                pass
            else:
                matches = _BACK_REFERENCE.findall(self.mapping)
                references = map(int, matches)
                if references and regex.groups < max(references):
                    raise ValidationError("The mapping contains a reference to a pattern group "
                                          "that does not exist")

    def __unicode__(self):
        return self.pattern

    class Meta(object):
        """Metadata options for the ``Filter`` model class."""

        order_with_respect_to = "source"


class Update(Model):
    """
    Records updates made to the repository for each dataset.

    This class overrides the :py:meth:`~Model.get_absolute_url` method of the
    :py:class:`Model` class.
    """

    dataset = related.ForeignKey(Dataset, related_name="updates", related_query_name="update")
    """The updated dataset."""
    source = related.ForeignKey(Source, blank=True, null=True, related_name="updates",
                                related_query_name="update")
    """
    The data source used to update the dataset.

    If None, the update was initiated with user-supplied data.
    """
    timestamp = fields.DateTimeField(auto_now_add=True, editable=False)
    """The date and time when this update occurred."""
    size = fields.BigIntegerField(default=-1, editable=False)
    """
    The size of the resource as reported by the data source, or -1 if this
    metadata is unavailable.
    """
    modified_at = fields.DateTimeField(blank=True, null=True, editable=False)
    """
    The modification date of the resource as reported by the data source, or
    None if this metadata is unavailable.
    """

    class Meta(object):
        get_latest_by = "timestamp"
        unique_together = ["dataset", "source", "timestamp"]


class Revision(Model):
    """
    Represents revisions of files maintained by this repository.

    This class overrides the :py:meth:`~Model.get_absolute_url` method of the
    :py:class:`Model` class.
    """

    file = related.ForeignKey(File, related_name='revisions', related_query_name='revision')
    """The file of which this revision is a part."""
    number = fields.PositiveIntegerField(editable=False)
    """The revision number of this revision."""
    data = files.FileField(upload_to=upload_path, storage=delta_storage)
    """The data contained within this file."""
    size = fields.BigIntegerField(editable=False)
    """The size, in bytes, of this revision."""
    update = related.ForeignKey(Update, related_name="revisions", related_query_name="revision")
    """The update that caused the addition of this revision."""
    format = related.ForeignKey(Format, related_name='revisions', related_query_name='revision',
                                default=1, on_delete=SET_DEFAULT)
    """The format of this revision."""
    tags = related.ManyToManyField(Tag, blank=True, related_name='revisions',
                                   related_query_name='revision')
    """The tags used to annotate this revision."""

    def __init__(self, *args, **kwargs):
        """
        Initialise a new revision instance.

        If a revision number is not given, the next available sequence number
        is used.
        If a format is not specified, the default format for the file is used.

        :keyword number: The revision number for this instance.
        :type number: int
        :keyword format: The format for this instance.
        :type format: Format
        """
        if kwargs:
            parent = kwargs["file"]
            if "number" not in kwargs:
                last_revision = parent.revisions.order_by("number").last()
                kwargs["number"] = last_revision.number + 1 if last_revision else 1
            if "format" not in kwargs:
                kwargs["format"] = parent.default_format
        super(Revision, self).__init__(*args, **kwargs)

    def get_absolute_url(self):
        """
        Return a URL that can be used to obtain more details about this
        revision.
        """
        # TODO: Implement revision URL
        # return reverse('bdr.backend:revision-detail',
        #                kwargs={'ds': self.datafile.dataset.slug, 'fn': self.datafile.name,
        #                        'rev': self.level})
        raise NotImplementedError

    class Meta(object):
        """Metadata options for the ``Revision`` model class."""

        unique_together = (('file', 'number'),)
        """Require that each revision number is unique for revisions of any given file."""


# noinspection PyUnusedLocal
# The sender parameter is unnecessary as the instance is guaranteed to be a
# Revision
@receiver(post_delete, sender=Revision)
def _remove_orphaned_files(sender, instance, **kwargs):
    instance.data.delete(save=False)
