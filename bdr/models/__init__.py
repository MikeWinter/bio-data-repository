"""
This package contains class definitions for the domain model of this
application.

The classes exported by this
"""

from datetime import datetime, timedelta
import re

# from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.db.models import Model, fields
from django.db.models.fields import files, related
from django.db.models.signals import post_delete
from django.dispatch import receiver

from ..utils import utc
# from ..utils.archives import Archive
from ..utils.storage import delta_storage, upload_path

__all__ = ["Category", "Dataset", "DataFile", "Filter", "Revision", "Source", "Tag"]
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
        # TODO: Implement
        # return reverse("bdr:tag-detail", kwargs={"pk": self.pk})
        raise NotImplementedError

    class Meta(object):
        """Metadata options for the Category model class."""
        ordering = ["name"]


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
    slug = fields.SlugField(unique=True)
    """A unique, keyword identifier for this dataset."""
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
    #             if source.has_changed():
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
        # TODO: Implement
        # return reverse('bdr.backend:dataset-detail', kwargs={'slug': self.slug})
        raise NotImplementedError

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

    class Meta(object):
        """Metadata options for the Dataset model class."""
        ordering = ["name"]
        """Order results lexicographically by name."""


class DataFile(Model):
    """
    Represents the files that constitute each dataset maintained by this
    repository.

    This class overrides the `~Model.get_absolute_url` method of the `Model`
    class.
    """

    name = fields.CharField(max_length=100, blank=False, editable=False)
    """The name of this file."""
    dataset = related.ForeignKey(Dataset, related_name='datafiles', related_query_name='datafile')
    """The dataset to which this file belongs."""
    # TODO: Enable default format
    # default_format = related.ForeignKey(Format, related_name='datafiles',
    #                                     related_query_name='datafile')
    """The format of this file."""
    tags = related.ManyToManyField(Tag, blank=True, related_name='datafiles',
                                   related_query_name='datafile')
    """The tags used to annotate this file."""

    def get_absolute_url(self):
        """
        Return a URL that can be used to obtain more details about this file.
        """
        # TODO: Implement
        # return reverse('bdr.backend:file-detail', kwargs={'ds': self.dataset.slug, 'fn': self.name})
        raise NotImplementedError

    class Meta(object):
        """Metadata options for the DataFile model class."""
        ordering = ["name"]
        """Place results in ascending order by name."""
        unique_together = (("dataset", "name"),)
        """Require that file names are unique within a given dataset."""


class Revision(Model):
    """
    Represents revisions of files maintained by this repository.

    This class overrides the `~Model.get_absolute_url` method of the `Model`
    class.
    """

    datafile = related.ForeignKey(DataFile, related_name='revisions', related_query_name='revision')
    """The file of which this revision is a part."""
    number = fields.PositiveIntegerField(editable=False)
    """The revision number of this revision."""
    data = files.FileField(upload_to=upload_path, storage=delta_storage)
    """The data contained within this file."""
    size = fields.BigIntegerField(editable=False)
    """The size, in bytes, of this revision."""
    updated_at = fields.DateTimeField(editable=False)
    """The modification date and time for this revision."""
    # format = related.ForeignKey(Format, related_name='revisions', related_query_name='revision')
    """The format of this file."""
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
            parent = kwargs["datafile"]
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
        unique_together = (('datafile', 'number'),)
        """Require that each revision number is unique for revisions of any given file."""


class Source(Model):
    """
    Represents a remote location that can be used to update one or more files
    within a dataset.
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
    size = fields.BigIntegerField(default=-1, editable=False)
    """The size of the resource as reported by this data source."""
    updated_at = fields.DateTimeField(blank=True, null=True, editable=False)
    """
    The modification date of the resource as reported by this data source; None
    if this metadata is unavailable.
    """

    def __init__(self, *args, **kwargs):
        super(Source, self).__init__(*args, **kwargs)
        # self.__connection = None

    def files(self):
        """
        Fetch the files obtainable from this data source.
        """
        pass

    # @property
    # def filename(self):
    #     """
    #     Return the name of the file referenced by this data source.
    #
    #     :return: The file name of the resource.
    #     :rtype:  basestring
    #     """
    #     path = urlsplit(self.url).path
    #     return os.path.basename(path)
    #
    # def changed(self, timestamp=None, size=-1):
    #     """
    #     Mark this source as changed.
    #
    #     If the timestamp or size is omitted, the metadata reported by the data
    #     source is used.
    #
    #     :param timestamp: An optional timestamp denoting when the resource was
    #                       updated.
    #     :type  timestamp: datetime | None
    #     :param size: The updated size of the resource (optional).
    #     :type  size: int
    #     """
    #     if timestamp is None:
    #         timestamp = self._connection.get_modification_date()
    #     if size == -1:
    #         size = self._connection.get_size()
    #     self.updated_at = timestamp
    #     self.size = size
    #     self.save(update_fields=("updated_at", "size"))
    #
    # def checked(self, timestamp=None):
    #     """
    #     Mark this source as checked.
    #
    #     If the timestamp is omitted, the current time is used.
    #
    #     :param timestamp: An optional timestamp denoting when this source was
    #                       checked.
    #     :type  timestamp: datetime | None
    #     """
    #     if timestamp is None:
    #         timestamp = datetime.now(utc)
    #     self.checked_at = timestamp
    #     self.save(update_fields=("checked_at",))
    #
    # def fetch(self):
    #     """
    #     Retrieve the resource from this data source.
    #
    #     :return: The resource referenced by this data source.
    #     :rtype:  file
    #     """
    #     return self._connection.get_content()
    #
    # def has_changed(self):
    #     """
    #     Query the remote data source to determine whether the resource has
    #     changed and return True if so.
    #
    #     :return: True if the resource has changed; otherwise False.
    #     :rtype:  bool
    #     """
    #     size = self._connection.get_size()
    #     if size != self.size:
    #         return True
    #     updated_at = self._connection.get_modification_date()
    #     if updated_at is not None and (self.updated_at is None or updated_at > self.updated_at):
    #         return True
    #     return False

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
        delta = timedelta(hours=self.frequency)
        return self.checked_at + delta <= datetime.now(utc)

    # @property
    # def _connection(self):
    #     if self.__connection is None:
    #         self.__connection = Transport.instance(self.url, self.username, self.password)
    #     return self.__connection

    class Meta(object):
        """Metadata options for the Source model class."""
        unique_together = (("dataset", "url"),)
        """Require that datasets do not have duplicate source locations."""


class Filter(Model):
    """
    Analyses (and optionally transforms) the names of files retrieved from data
    sources to determine whether they should be added to the dataset associated
    with that source.
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

    class Meta(object):
        """Metadata options for the Filter model class."""
        order_with_respect_to = "source"


# noinspection PyUnusedLocal
@receiver(post_delete, sender=Revision)
def _remove_orphaned_files(sender, instance, **kwargs):
    instance.data.delete(save=False)
