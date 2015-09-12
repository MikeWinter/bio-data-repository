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
from django.db.models import Model, fields
from django.db.models.fields import files, related
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.text import slugify

from .utils import utc, DownloadedFile
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

    The datasets belonging to a category can be retrieved using the `datasets`
    property of an instance.

    This class overrides the `~Model.get_absolute_url` method of the `Model`
    class.
    """

    name = fields.CharField(max_length=50, unique=True)
    """The name of this category."""

    def get_absolute_url(self):
        """
        Return a URL that can be used to obtain more details about this
        category.
        """
        return reverse("bdr:category", kwargs={"pk": self.pk, "name": slugify(self.name)})

    def __str__(self):
        return self.name

    class Meta(object):
        """Metadata options for the Category model class."""
        ordering = ["name"]
        verbose_name_plural = "categories"


class Tag(Model):
    """
    Tags annotate datasets, data files and revisions.

    The entities associated with a given tag can be retrieved via their
    respective properties `datasets`, `datafiles` and `revisions`.

    This class overrides the `~Model.get_absolute_url` method of the `Model`
    class.
    """

    name = fields.CharField(max_length=25, unique=True)
    """The name of this tag."""

    def get_absolute_url(self):
        """
        Return a URL that can be used to obtain more details about this tag.
        """
        # TODO: Implement
        # return reverse('bdr.backend:tag-detail', kwargs={'pk': self.pk})
        raise NotImplementedError

    def __str__(self):
        return self.name

    class Meta(object):
        """Metadata options for the Tag model class."""
        ordering = ["name"]


class Dataset(Model):
    """
    A dataset is collection of data files maintained by the repository.

    The contents of a dataset can be updated automatically from a remote source
    if one has been specified.

    This class overrides the `~Model.get_absolute_url` method of the `Model`
    class.
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

    # def update(self):
    #     """
    #     Query the sources for this dataset and add revisions for any modified
    #     files.
    #     """
    #     for source in [src for src in self.sources.all() if src.has_update_elapsed()]:
    #         with transaction.atomic():
    #             source.checked()
    #             if source._has_changed():
    #                 for file_ in source.files():
    #                     self.add_file(file_)
    #                 source.changed()
    #
    # def add_file(self, file_):
    #     # TODO: Add default format (raw) to defaults
    #     defaults = {"dataset": self}
    #     instance, _ = self.files.get_or_create(name=file_.name)
    #     instance.add_revision()

    def get_absolute_url(self):
        """
        Return a URL that can be used to obtain more details about this
        dataset.
        """
        return reverse("bdr:dataset", kwargs={"pk": self.pk, "name": slugify(self.name)})

    # def _map(self, filename):
    #     """
    #     Compare the filename against the filters for this dataset and transform
    #     it if appropriate.
    #
    #     If there are no matching filters, None is returned; if there are no
    #     filters associated with
    #
    #     :type filename: str
    #     :rtype: str | None
    #     """
    #     if not self.filters.exists():
    #         return filename
    #     for filter_id in self.get_filter_order():
    #         filter_ = self.filters.get(filter_id)
    #         if filter_.match(filename):
    #             return filter_.map(filename)
    #     return None
    #
    # def _process_archive(self, archive):
    #     """
    #     Add the contents of an archive to this dataset, updating or adding
    #     files as required.
    #
    #     :param archive: The archive to process.
    #     :type  archive: Archive
    #     """
    #     # TODO: Add default format (raw) to defaults
    #     defaults = {"dataset": self}
    #     # The Archive iterator returns str, not Member as inferred
    #     for member_name in archive:
    #         # noinspection PyTypeChecker
    #         filename = self._map(member_name)
    #         if filename:
    #             file_, _ = self.files.get_or_create(name=filename, defaults=defaults)
    #             # noinspection PyTypeChecker
    #             file_.add_revision(archive[member_name])

    def __str__(self):
        return self.name

    class Meta(object):
        """Metadata options for the Dataset model class."""
        ordering = ["name"]
        """Order results lexicographically by name."""


class File(Model):
    """
    Represents the files that constitute each dataset maintained by this
    repository.

    This class overrides the `~Model.get_absolute_url` method of the `Model`
    class.
    """

    name = fields.CharField(max_length=100, blank=False, editable=False)
    """The name of this file."""
    dataset = related.ForeignKey(Dataset, related_name="files", related_query_name="file")
    """The dataset to which this file belongs."""
    # TODO: Enable default format
    # default_format = related.ForeignKey(Format, related_name='datafiles',
    #                                     related_query_name='datafile')
    """The format of this file."""
    tags = related.ManyToManyField(Tag, blank=True, related_name="files",
                                   related_query_name="file")
    """The tags used to annotate this file."""

    def get_absolute_url(self):
        """
        Return a URL that can be used to obtain more details about this file.
        """
        # TODO: Implement
        # return reverse('bdr.backend:file-detail', kwargs={'ds': self.dataset.slug, 'fn': self.name})
        raise NotImplementedError

    def __str__(self):
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

    This class overrides the `~Model.get_absolute_url` method of the `Model`
    class.
    """

    url = fields.URLField()
    """A URL specifying the update source for files in this dataset."""
    dataset = related.ForeignKey(Dataset, editable=False, related_name='sources',
                                 related_query_name='source')
    """The dataset to which this update source relates."""
    username = fields.CharField(max_length=50, blank=True)
    """An optional user name for authentication."""
    password = fields.CharField(max_length=64, blank=True)
    """An optional password for authentication."""
    frequency = fields.PositiveSmallIntegerField(default=0)
    """
    How often, in hours, this source should be checked for updates; skipped if
    zero (0).
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

    def files(self):
        """
        Fetch the files obtainable from this data source.

        The files returned will consist of only those that pass the filters
        applicable to this data source.

        :return: A filtered list of `DownloadedFile` instances obtained from this data source.
        :rtype: list of DownloadedFile
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
                new_file = DownloadedFile(member.file, mapped_name, member.mtime)
                file_list.append(new_file)
        return file_list

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
        Return True if this data source is due to be checked.

        If the update frequency is zero, this method returns False.

        :return: True if this data source should be checked for updates; false
                 otherwise.
        :rtype:  bool
        """
        if not self.frequency:
            return False
        if not self.checked_at:
            return True
        delta = timedelta(hours=self.frequency)
        return self.checked_at + delta <= datetime.now(utc)

    def has_changed(self):
        """
        Determine whether the resource at this source has changed.

        :return: True if the resource has changed; otherwise False.
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
        Return an archive read from `data`.

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

    def __str__(self):
        return self.url

    class FileRejected(Exception):
        """Raised when a file is not matched by any filter."""
        pass

    class Meta(object):
        """Metadata options for the Source model class."""
        unique_together = (("dataset", "url"),)
        """Require that datasets do not have duplicate source locations."""


class Filter(Model):
    """
    Analyses (and optionally transforms) the names of files retrieved from data
    sources to determine whether they should be added to the dataset associated
    with that source.

    This class overrides the `~Model.get_absolute_url` method of the `Model`
    class.
    """

    pattern = fields.CharField(max_length=100, validators=[_validate_regex])
    """
    A regular expression defining file names accepted by this filter. Capture
    groups can be referenced by the mapping specification.
    """
    inverted = fields.BooleanField(default=False)
    """
    If True, a file is accepted by this filter if the name does not match the
    pattern expression.
    """
    mapping = fields.CharField(max_length=100, blank=True)
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
                pass  # If compilation fails, don't bother validating the mapping string.
            else:
                matches = _BACK_REFERENCE.findall(self.mapping)
                references = map(int, matches)
                if references and regex.groups < max(references):
                    raise ValidationError("The mapping contains a reference to a pattern group "
                                          "that does not exist")

    def __str__(self):
        return self.pattern

    class Meta(object):
        """Metadata options for the Filter model class."""
        order_with_respect_to = "source"


class Update(Model):
    """
    Records updates made to the repository for each dataset.

    This class overrides the `~Model.get_absolute_url` method of the `Model`
    class.
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

    This class overrides the `~Model.get_absolute_url` method of the `Model`
    class.
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
    # format = related.ForeignKey(Format, related_name='revisions', related_query_name='revision')
    # """The format of this file."""
    tags = related.ManyToManyField(Tag, blank=True, related_name='revisions',
                                   related_query_name='revision')
    """The tags used to annotate this revision."""

    def __init__(self, *args, **kwargs):
        """
        Initialise a new revision instance.

        If a revision number is not given, the next available sequence number
        is used.

        :keyword number: The revision number for this instance.
        :type number: int
        """
        if kwargs and "number" not in kwargs:
            parent = kwargs["file"]
            last_revision = parent.revisions.order_by("number").last()
            kwargs["number"] = last_revision.number + 1 if last_revision else 1
        super(Revision, self).__init__(*args, **kwargs)

    def get_absolute_url(self):
        """
        Return a URL that can be used to obtain more details about this revision.
        """
        # TODO: Implement
        # return reverse('bdr.backend:revision-detail',
        #                kwargs={'ds': self.datafile.dataset.slug, 'fn': self.datafile.name,
        #                        'rev': self.level})
        raise NotImplementedError

    class Meta(object):
        """Metadata options for the Revision model class."""
        unique_together = (('file', 'number'),)
        """Require that each revision number is unique for revisions of any given file."""


# noinspection PyUnusedLocal
# The sender parameter is unnecessary as the instance is guaranteed to be a
# Revision
@receiver(post_delete, sender=Revision)
def _remove_orphaned_files(sender, instance, **kwargs):
    instance.data.delete(save=False)
