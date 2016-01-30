"""
Storage handling for models based on delta-compression.
"""

from hashlib import sha1 as hash_algorithm
from tempfile import NamedTemporaryFile
import errno
import fnmatch
import io
import os.path
import shutil
import subprocess

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from locket import lock_file

from .. import app_settings

__all__ = ["delta_storage", "upload_path"]
__author__ = "Michael Winter (mail@michael-winter.me.uk)"
__license__ = """
    Biological Dataset Repository: data archival and retrieval.
    Copyright (C) 2015  Michael Winter

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
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

        with Lock(self.path(path + filename)):
            if not self.exists(name):
                raise FileNotFoundError(name)

            base = None
            for current in self._get_related_files(name):
                full_path = self.path(os.path.join(path, current))
                # Decode the current file based on the prior chain member, if
                # any, and remove the intermediary file
                decoded_path = self._decode(full_path, base, unlink_base=True)

                if current == filename:
                    # Reopen the decoded file and make it self-deleting again
                    return FileDeletionWrapper(io.open(decoded_path, "rb"))

                # Use the decoded file for the next one in the chain
                base = decoded_path

        raise FileNotFoundError(name)  # This should not be possible here.

    def _save(self, name, content):
        path, filename = os.path.split(name)
        full_path = self.path(name)

        with NamedTemporaryFile(delete=False) as copy:
            shutil.copyfileobj(content, copy)

        try:
            with Lock(self.path(path + filename)):
                directory = os.path.dirname(full_path)
                if not os.path.exists(directory):
                    try:
                        os.makedirs(directory)
                    except OSError as error:
                        if error.errno != errno.EEXIST:
                            raise
                if not os.path.isdir(directory):
                    raise IOError("{0:s} exists and is not a directory.".format(directory))

                files = self._get_related_files(name)
                if files:
                    head = os.path.join(directory, files[0])
                    # Decode head into a temporary file
                    temp = self._decode(head)

                    self._encode(temp, head, base=copy.name, unlink_source=True)

                # Encode the added file
                self._encode(copy.name, full_path)
        finally:
            # Remove the on-disk copy of content
            os.unlink(copy.name)

        if settings.FILE_UPLOAD_PERMISSIONS is not None:
            os.chmod(full_path, settings.FILE_UPLOAD_PERMISSIONS)
        return name

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

        with Lock(self.path(path + filename)):
            if self.exists(name):
                files = self._get_related_files(name)
                index = files.index(filename)
                # If the target file is not the last member of the chain, the
                # file that follows it will need to be recoded using the file
                # that precedes the target in the chain.
                if index != len(files) - 1:
                    # Decode chain members up to the target file discarding
                    # temporary files along the way.
                    base = None
                    for current in files[:index]:
                        current_path = self.path(os.path.join(path, current))
                        base = self._decode(current_path, base, unlink_base=True)
                    prior = base

                    try:
                        # Decode the target file using its predecessor (if
                        # applicable).
                        target = self._decode(full_path, base=prior)

                        after = self.path(os.path.join(path, files[index + 1]))
                        # Decode the trailing file deleting the decoded version
                        # of the target
                        copy = self._decode(after, base=target, unlink_base=True)

                        # Recode the trailing file deleting its intermediary
                        self._encode(copy, after, base=prior, unlink_source=True)
                    finally:
                        if prior:
                            os.unlink(prior)

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

    @staticmethod
    def _decode(source, base=None, unlink_base=False):
        output = NamedTemporaryFile(delete=False)
        output.close()

        args = [app_settings.XDELTA_BIN, "-fdS", "djw", source, output.name]
        if base:
            args[3:3] = ("-s", base)
        try:
            subprocess.check_call(args)
        except subprocess.CalledProcessError:
            os.unlink(output.name)
            raise
        finally:
            if unlink_base and base:
                os.unlink(base)

        return output.name

    @staticmethod
    def _encode(source, destination, base=None, unlink_source=False):
        args = [app_settings.XDELTA_BIN, "-feS", "djw", source, destination]
        if base:
            args[3:3] = ("-s", base)
        try:
            subprocess.check_call(args)
        finally:
            if unlink_source:
                os.unlink(source)

    def _get_related_files(self, name):
        path, filename = os.path.split(name)
        root = os.path.splitext(filename)[0]
        related_files = fnmatch.filter(self.listdir(path)[1], ".".join((root, "??????")))
        return sorted(related_files, reverse=True)


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


class FileDeletionWrapper(object):
    """
    Wraps a :py:class:`file`-like object in such a way that garbage collecting
    or closing the wrapper closes and deletes the underlying file.
    """

    # noinspection PyShadowingBuiltins
    def __init__(self, file):
        self._file = file
        self._closed = False

    def __del__(self):
        self.close()

    def __getattr__(self, item):
        # Delegate attribute lookups to the underlying file
        return getattr(self._file, item)

    def __enter__(self):
        self._file.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        suppress = self._file.__exit__(exc_type, exc_val, exc_tb)
        self.close()
        return suppress

    def close(self):
        if not self._closed:
            self._closed = True
            self._file.close()
            os.unlink(self._file.name)


class FileNotFoundError(IOError):
    """File does not exist."""

    def __init__(self, name):
        code = errno.ENOENT
        message = "{0}: {1}".format(os.strerror(code), name)
        super(FileNotFoundError, self).__init__(code, message)


delta_storage = DeltaFileSystemStorage()
