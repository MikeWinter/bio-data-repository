"""
Storage handling for models based on delta-compression.
"""

import errno
from hashlib import sha1 as hash_algorithm
import os.path

from django.core.files.storage import FileSystemStorage

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

    def delete(self, name):
        """
        Deletes the specified file from the storage system.

        If the containing directory becomes empty as a result, it is also
        removed.

        :param name: The name of the file to delete.
        :type name: str | unicode
        """
        super(DeltaFileSystemStorage, self).delete(name)

        path = os.path.dirname(self.path(name))
        try:
            os.rmdir(path)
        except OSError as error:
            # Failing to delete a directory that still contains files is not
            # considered an error. This approach avoids a race condition where
            # a file may be created between finding the directory empty and
            # deleting it.
            if error.errno != errno.ENOTEMPTY:
                raise


delta_storage = DeltaFileSystemStorage()
