"""
A set of tools for accessing archive formats. The archive types supported
out-of-the-box are those read by the gzip, zipfile and tarfile modules.

Additional archive formats can be supported by subclassing Archive and adding
the fully-qualified class name of the new type to the ARCHIVE_READERS list
setting.
"""

from datetime import datetime
import gzip
import importlib
import os
import re
import tarfile
import tempfile
from UserDict import DictMixin
import zipfile

from .. import app_settings
from . import utc

__all__ = ["Archive", "Member"]
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


class Archive(DictMixin, object):
    """
    An adapter for handling archive formats.

    Archives are map-like: iteration is supported and returns the names of each
    member of the archive, which can in turn be used to index the archive in
    order to retrieve that member.
    """
    @classmethod
    def instance(cls, file_, path=None):
        """
        Return an archive capable of reading the given file.

        :param file_: A file-like object containing the archive.
        :type  file_: file
        :param path: The path to the archive.
        :rtype: Archive
        """
        file_.seek(0)
        for reader in app_settings.ARCHIVE_READERS:
            namespaces = reader.split('.')
            module = importlib.import_module('.'.join(namespaces[:-1]))

            if hasattr(module, namespaces[-1]):
                obj = getattr(module, namespaces[-1])(file_, path)
                if obj.can_read():
                    return obj

        raise RuntimeError("BDR_ARCHIVE_READERS setting does not include catch-all reader.")

    def __init__(self, file_, path=None):
        """
        Create an archive, reading the specified file.

        :param file_: A file-like object containing an archive.
        :type file_:  file
        :param path: The absolute path of the archive.
        :type path:  str
        """
        self._file = file_
        if not path:
            abspath = os.path.abspath(file_.name)
            if os.path.exists(abspath):
                path = abspath
        self._path = path

    def __getitem__(self, key):
        """
        Return a Member instance describing a file within the archive.

        :param key: The name of the file to be retrieved.
        :type key:  str
        :return: The file member named by `key`.
        :rtype:  Member
        """
        raise NotImplementedError

    def __setitem__(self, key, value):
        raise TypeError("Archive is read-only.")

    def __delitem__(self, key):
        raise TypeError("Archive is read-only.")

    def can_read(self):
        """
        Return True if this instance can be used to read the archive; otherwise
        False.

        :return: True if this instance can be used to read the archive.
        :rtype:  bool
        """
        raise NotImplementedError

    def keys(self):
        """
        Return a copy of the list of member names.

        :return: A list of file names in this archive.
        :rtype:  list
        """
        raise NotImplementedError

    @property
    def file(self):
        """
        Return the file wrapped by this archive.

        :return: The file wrapped by this archive.
        :rtype: file
        """
        return self._file

    @property
    def path(self):
        """
        Return the path to this archive, if available.

        :return: The path to this archive if available; ``None`` otherwise.
        :rtype: str | None
        """
        return self._path

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._file.close()


class Member(object):
    """A file member of an archive."""

    def __init__(self, name, size, mtime, member):
        self._name, self._size, self._mtime, self._member = name, size, mtime, member

    @property
    def file(self):
        """
        A read-only, file-like object containing the data for this member.

        :rtype: file
        """
        return self._member

    @property
    def name(self):
        """
        The name of this member.

        :rtype: str
        """
        return self._name

    @property
    def mtime(self):
        """
        A datetime instance representing the modification time of this member.

        :rtype: datetime
        """
        return self._mtime

    @property
    def size(self):
        """
        The decompressed size of this member in bytes.

        :rtype: int
        """
        return self._size


class GzipArchive(Archive):
    """An adaptor for reading Gzip format archives."""

    def __init__(self, file_, path=None):
        """
        :param file_: A file-like object containing an archive.
        """
        super(GzipArchive, self).__init__(file_, path)
        self._zip = None
        self._name = re.sub(r'\.gz\w*$', '', os.path.basename(self._path or file_.name))

    def __getitem__(self, key):
        if not self.can_read():
            raise IOError('Not a gzipped archive.')
        if key != self._name:
            raise KeyError('%s not found.' % key)
        return GzipMember(self._name, 0, None, self._zip)

    def can_read(self):
        """
        Return True if this instance can be used to read the archive; otherwise
        False.
        """
        if self._zip is None:
            self._zip = gzip.GzipFile(fileobj=self._file, mode='rb')
            try:
                self._zip.read(1)
            except IOError:
                return False
            finally:
                self._zip.rewind()
        return True

    def keys(self):
        """Return a copy of the list of member names."""
        if not self.can_read():
            raise IOError('Not a gzipped archive.')
        return [self._name]

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._zip.close()
        super(GzipArchive, self).__exit__(exc_type, exc_val, exc_tb)


class GzipMember(Member):
    """A file member of a gzip archive."""

    def __init__(self, *args, **kwargs):
        super(GzipMember, self).__init__(*args, **kwargs)
        self._data = self._unpack(self._member)

    @property
    def file(self):
        """A file-like object containing the data for this member."""
        return self._data

    @property
    def mtime(self):
        """
        A datetime instance representing the modification time of this member.
        """
        return datetime.fromtimestamp(self._member.mtime, utc)

    @property
    def size(self):
        """The decompressed size of this member in bytes."""
        return self._member.size

    @staticmethod
    def _unpack(file_):
        data = tempfile.TemporaryFile()
        for block in file_:
            data.write(block)
        data.seek(0)
        return data


class MockArchive(Archive):
    """
    An adaptor that imitates reading from an archive when dealing with single
    files.
    """

    def __init__(self, file_, path=None):
        """
        :param file_: A file-like object containing an archive.
        """
        super(MockArchive, self).__init__(file_, path)
        self._name = os.path.basename(self._path)

    def __getitem__(self, key):
        if key != self._name:
            raise KeyError('%s not found.' % key)
        stats = None
        if hasattr(self._file, 'fileno') and callable(self._file.fileno):
            stats = os.fstat(self._file.fileno())
        elif self._path:
            stats = os.stat(self._path)
        return Member(self._name, stats.st_size if stats else -1,
                      datetime.fromtimestamp(stats.st_mtime, utc) if stats else None, self._file)

    def can_read(self):
        """
        Return True if this instance can be used to read the archive; otherwise
        False.

        This implementation always returns True.
        """
        return True

    def keys(self):
        """Return a copy of the list of member names."""
        return [self._name]


class TarArchive(Archive):
    """An adaptor for reading tar format archives."""

    def __init__(self, file_, path=None):
        super(TarArchive, self).__init__(file_, path)
        self._tar = None
        self._names = None

    def __getitem__(self, key):
        if not self.can_read():
            raise IOError('Not a tar archive.')
        info = self._tar.getmember(key)
        return Member(info.name, info.size, info.mtime, self._tar.extractfile(info))

    def can_read(self):
        """
        Return True if this instance can be used to read the archive; otherwise
        False.
        """
        if self._tar is None:
            try:
                self._tar = tarfile.open(fileobj=self._file)
            except tarfile.ReadError:
                return False
        return True

    def keys(self):
        """Return a copy of the list of member names."""
        if not self.can_read():
            raise IOError('Not a tar archive.')
        if self._names is None:
            self._names = [member.name for member in self._tar.getmembers() if member.isfile()]
        return self._names

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._tar.close()
        super(TarArchive, self).__exit__(exc_type, exc_val, exc_tb)


class ZipArchive(Archive):
    """An adaptor for reading Zip format archives."""

    def __init__(self, file_, path=None):
        super(ZipArchive, self).__init__(file_, path)
        self._zip = None
        self._names = None

    def __getitem__(self, key):
        if key not in self.keys():
            raise KeyError('%s not found.' % key)
        info = self._zip.getinfo(key)
        return Member(info.filename, info.file_size, datetime(*info.date_time, tzinfo=utc),
                      self._zip.open(info))

    def can_read(self):
        """
        Return True if this instance can be used to read the archive; otherwise
        False.
        """
        readable = zipfile.is_zipfile(self._file)
        self._file.seek(0)
        return readable

    def keys(self):
        """Return a copy of the list of member names."""
        if not self.can_read():
            raise IOError('Not a Zip archive.')
        self._open()
        if self._names is None:
            self._names = [name for name in self._zip.namelist() if not name.endswith('/')]
        return self._names

    def _open(self):
        if self._zip is None:
            self._zip = zipfile.ZipFile(self._file)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._zip.close()
        super(ZipArchive, self).__exit__(exc_type, exc_val, exc_tb)
