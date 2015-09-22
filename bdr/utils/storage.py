"""
Storage handling for models based on delta-compression.
"""

from hashlib import sha1 as hash_algorithm
from locket import lock_file
from tempfile import TemporaryFile
import errno
import fnmatch
import io
import os.path
import shutil

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from xdelta import DeltaFile

__all__ = ["delta_storage", "upload_path"]
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


# noinspection PyUnusedLocal
def upload_path(instance, filename):
    """
    Compute the relative path to the given revision file.

    The path must not depend upon mutable information such as editable
    names.

    :param instance: The revision.
    :type instance: bdr.models.Revision
    :param filename: The name of the uploaded file.
    :type filename: str
    :return: The relative path to this revision.
    :rtype: str
    """
    path = "{0:06x}".format(instance.file.dataset.id)
    basename = hash_algorithm(instance.file.name).hexdigest()
    name = "{0:s}.{1:06x}".format(basename, instance.number)
    return os.path.join(path, name)


# noinspection PyAbstractClass
class DeltaFileSystemStorage(FileSystemStorage):
    """
    Provides a filesystem-backed storage mechanism that uses delta compression
    to minimise disk space.

    If two files within the same directory share the same root file name, they
    will form a reverse chain where each file is encoded as a delta based on
    the file that follows it (according to file name in lexicographical order).
    The last file in the chain is compressed according to standard lossless
    compression techniques.

    The root of a file name is defined to be that which precedes the last dot
    in the name.

    :Example:
    >>> import os.path
    >>> path = "/foo/test.example.ext"
    >>> name = os.path.basename(path)
    >>> root, ext = os.path.splitext(name)
    >>> root == "test.example"
    True
    """

    def _open(self, name, mode="rb"):
        """
        Return a :py:class:``~django.core.files.File` instance that wraps the
        file with the given name.

        :param name: The name of the file to open.
        :type name: str | unicode
        :param mode: The mode in which the file is to be opened.
        :type mode: str
        :return: The open file.
        :rtype: django.core.files.File
        :raises FileNotFoundError: if ``name`` does not exist.
        """
        path, filename = os.path.split(name)
        with Lock(self.path(name)):
            if not self.exists(name):
                raise FileNotFoundError(name)

            base = None
            for current in self._get_related_files(name):
                full_path = self.path(os.path.join(path, current))
                delta = DeltaFile(io.open(full_path, "rb"))
                delta.source = base

                if current == filename:
                    return delta

                with delta:
                    base = TemporaryFile()
                    shutil.copyfileobj(delta, base)
                base.seek(0)

        raise FileNotFoundError(name)  # This should not be possible here.

    def _save(self, name, content):
        full_path = self.path(name)

        directory = os.path.dirname(full_path)
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError as error:
                if error.errno != errno.EEXIST:
                    raise
        if not os.path.isdir(directory):
            raise IOError("{0:s} exists and is not a directory.".format(directory))

        with Lock(full_path):
            files = self._get_related_files(name)
            if files:
                head = os.path.join(directory, files[0])
                with DeltaFile(io.open(head, "rb")) as delta:
                    copy = TemporaryFile()
                    shutil.copyfileobj(delta, copy)

                copy.seek(0)
                with DeltaFile(io.open(head, "wb")) as delta:
                    delta.source = content
                    shutil.copyfileobj(copy, delta)

            content.seek(0)
            with DeltaFile(io.open(full_path, "wb")) as delta:
                shutil.copyfileobj(content, delta)

        if settings.FILE_UPLOAD_PERMISSIONS is not None:
            os.chmod(full_path, settings.FILE_UPLOAD_PERMISSIONS)
        return name

    def _get_related_files(self, name):
        path, filename = os.path.split(name)
        root = os.path.splitext(filename)[0]
        related_files = fnmatch.filter(self.listdir(path)[1], ".".join((root, "??????")))
        return sorted(related_files, reverse=True)

    def delete(self, name):
        """
        Deletes the specified file from the storage system.

        If the containing directory becomes empty as a result, it is also
        removed.

        :param name: The name of the file to delete.
        :type name: str | unicode
        """
        path, filename = os.path.split(name)
        full_path = self.path(name)
        with Lock(full_path):
            if self.exists(name):
                files = self._get_related_files(name)
                index = files.index(filename)
                if index != len(files) - 1:
                    base = None
                    for current in files[:index]:
                        current_path = self.path(os.path.join(path, current))
                        delta = DeltaFile(io.open(current_path, "rb"))
                        delta.source = base

                        with delta:
                            base = TemporaryFile()
                            shutil.copyfileobj(delta, base)
                        base.seek(0)
                    prior = base

                    with DeltaFile(io.open(full_path, "rb")) as delta:
                        delta.source = prior
                        temp = TemporaryFile()
                        shutil.copyfileobj(delta, temp)

                    after = self.path(os.path.join(path, files[index + 1]))
                    temp.seek(0)
                    with DeltaFile(io.open(after, "rb")) as delta:
                        delta.source = temp
                        copy = TemporaryFile()
                        shutil.copyfileobj(delta, copy)

                    if prior:
                        prior.seek(0)
                    copy.seek(0)
                    with DeltaFile(io.open(after, "wb")) as delta:
                        delta.source = prior
                        shutil.copyfileobj(copy, delta)

                super(DeltaFileSystemStorage, self).delete(name)

        path = os.path.dirname(full_path)
        try:
            os.rmdir(path)
        except OSError as error:
            # Failing to delete a directory that still contains files is not
            # considered an error. This approach avoids a race condition where
            # a file may be created between finding the directory empty and
            # deleting it.
            if error.errno != errno.ENOTEMPTY:
                raise

    def url(self, name):
        """
        Return the URL where the contents of the file referenced by ``name``
        can be accessed.

        This method always raises :py:exc:`NotImplementedError`.

        :param name: The name of the file to access by URL.
        :type name: str | unicode
        :raises NotImplementedError: when called.
        """
        raise NotImplementedError("URL access is forbidden for delta-encoded files.")


class Lock(object):
    """
    A lock based around lock files.

    Instances of this class are context managers, with lock acquisition
    occurring on entrance to a ``with`` block::

        with Lock("/path/to/file"):
            do_protected_action()

    The lock is released automatically when the block is left.
    """
    def __init__(self, path, **kwargs):
        base = os.path.splitext(path)[0]
        self._path = ".".join((base, "lock"))
        self._lock = lock_file(self._path, **kwargs)

    def __enter__(self):
        self._lock.acquire()
        return self

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()
        try:
            os.remove(self._path)
        except OSError as err:
            # Ignore deletion failure on Windows
            if err.errno not in (errno.EACCES, errno.ENOENT):
                raise


class FileNotFoundError(IOError):
    """File does not exist."""
    def __init__(self, name):
        code = errno.ENOENT
        message = "{0}: {1}".format(os.strerror(code), name)
        super(FileNotFoundError, self).__init__(code, message)


delta_storage = DeltaFileSystemStorage()
