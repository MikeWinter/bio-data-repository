"""
A set of classes for abstracting communication with remote servers. While the
urllib-family of modules provides similar functionality, they not provide for
querying the source for its metadata (size and modification date, in this case)
prior to fetching the resource itself.

All exceptions raised by these types inherit from the TransportError class.

Support for the FTP and HTTP protocols are included by default. This can be
extended to any communications protocol, however, by subclassing Transport and
adding the fully-qualified class name for the new type to the REMOTE_TRANSPORTS
settings list.
"""

from datetime import datetime
import ftplib
import httplib
import importlib
import os.path
import re
import socket
import tempfile
import urlparse

from django.utils.http import parse_http_date_safe
import httplib2

from .. import app_settings
from . import utc

__all__ = ["Transport", "TransportError"]
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


class TransportError(IOError):
    """Base class for all transport-related errors."""
    pass


class AuthenticationError(TransportError):
    """Authentication credentials are missing or incorrect."""
    pass


class ConnectionError(TransportError):
    """Could not establish a connection."""
    pass


class NotFoundError(TransportError):
    """The requested resource could not be found remotely."""
    pass


class Transport(object):
    """
    An abstraction for retrieving resources, and their metadata, from remote
    sources.
    """
    @classmethod
    def instance(cls, url, user='', password=''):
        """
        Create an instance of a data transport mechanism. The transport type
        returned is determined by the scheme component given by `url`.

        :param url: The URL of the resource to be obtained.
        :type  url: basestring
        :param user: The user name required to access the resource specified in
                     `url` (optional).
        :type  user: basestring
        :param password: The password required to access the resource specified
                         in `url` (optional).
        :type  password: basestring
        :return: A transport mechanism capable of accessing the specified
                 resource, or None if no matching transport type can be found.
        :rtype:  Transport | None
        """
        scheme, _, _, _, _ = urlparse.urlsplit(url)
        if scheme in app_settings.REMOTE_TRANSPORTS:
            package = app_settings.REMOTE_TRANSPORTS[scheme].split('.')
            module = importlib.import_module('.'.join(package[:-1]))

            if hasattr(module, package[-1]):
                return getattr(module, package[-1])(url, user, password)
        return None

    def __init__(self, url, user, password):
        """
        Create an instance of a data transport mechanism.

        :param url: The URL of the resource to be obtained.
        :type  url: str
        :param user: The user name required to access the resource specified in
                     `url` (optional).
        :type  user: str
        :param password: The password required to access the resource specified
                         in `url` (optional).
        :type  password: str
        """
        self._content = None
        self._password = password
        self._url = url
        self._user = user

    def get_content(self):
        """
        Return a temporary file containing the requested resource. This data
        will be lost if the content object is closed.

        :return: A file-like object containing the requested resource.
        :rtype:  file
        """
        if self._content is None:
            self._content = tempfile.TemporaryFile()
            self._do_get_content()
            self._content.seek(0)
        return self._content

    def get_modification_date(self):
        """
        Return the date and time of the last modification to this resource as
        reported by the remote source.

        :return: The modification date and time, or None if unknown.
        :rtype:  datetime | None
        :raises TransportError: If an error occurs while communicating with the
                                server.
        """
        raise NotImplementedError

    def get_size(self):
        """
        Return the size of this resource as reported by the remote source.

        :return: The size (in bytes) of this resource, or -1 if unknown.
        :rtype:  int
        :raises TransportError: If an error occurs while communicating with the
                                server.
        """
        raise NotImplementedError

    def _do_get_content(self):
        """
        Retrieve the resource, writing it to `_content`. Subclasses must
        override this method.
        """
        raise NotImplementedError


class FtpTransport(Transport):
    """
    An abstraction for retrieving resources, and their metadata, from FTP
    servers.
    """
    _DEFAULT_TIMEOUT = 30
    _date_reply = None
    _feat_reply = None
    _size_reply = None

    def __init__(self, *args, **kwargs):
        """
        Create an instance of the FTP transport mechanism.

        :param url: The URL of the resource to be obtained.
        :type  url: str
        :param user: The user name required to access the resource specified in
                     `url` (optional).
        :type  user: str
        :param password: The password required to access the resource specified
                         in `url` (optional).
        :type  password: str
        """
        super(FtpTransport, self).__init__(*args, **kwargs)
        components = urlparse.urlsplit(self._url)
        self._host, self._port = components.hostname, components.port or ftplib.FTP_PORT
        self._path, self._name = os.path.dirname(components.path), os.path.basename(components.path)
        self._features = None
        self._modification_date = None
        self._size = -1
        self.__connection = None

    @property
    def features(self):
        """
        A list of feature strings representing FTP extensions supported by the
        server.

        See RFC 5797 for a summary of these feature strings and RFC 2389 for a
        description of the FEAT command.

        :return: A list of feature strings that indicated supported commands.
        :rtype:  list
        :raises TransportError: If an error occurs while communicating with the
                                server.
        """
        if self._features is None:
            if self._feat_reply is None:
                self._feat_reply = re.compile(r'^211([ -])[ \t\x21-\x7e]*'
                                              r'((?:[\r\n]+[ \t\x21-\x7e]+)+)'
                                              r'[\r\n]+211[ \t\x21-\x7e]*[\r\n]*$')

            try:
                reply = self._connection.sendcmd('FEAT')
            except ftplib.error_perm:
                self._features = []
            else:
                match = self._feat_reply.match(reply)
                self._features = (re.split(r'[\n\r]+ ', match.group(2).lstrip().lower())
                                  if match and match.group(1) == '-' else [])
        return self._features

    def get_modification_date(self):
        """
        Return the date and time of the last modification to this resource as
        reported by the remote source.

        :return: The modification date and time, or None if unknown.
        :rtype:  datetime | None
        :raises TransportError: If an error occurs while communicating with the
                                server.
        """
        if self._modification_date is None and 'mdtm' in self.features:
            if self._date_reply is None:
                self._date_reply = re.compile(r'^213 (\d{14})(?:\.\d+)?[\n\r]*')

            try:
                reply = self._connection.sendcmd('MDTM ' + self._name)
            except ftplib.error_perm as error:
                raise NotFoundError(error)
            match = self._date_reply.match(reply)
            self._modification_date = datetime.strptime(
                match.group(1)[:14], '%Y%m%d%H%M%S').replace(tzinfo=utc) if match else None
        return self._modification_date

    def get_size(self):
        """
        Return the size of this resource as reported by the remote source.

        :return: The size (in bytes) of this resource, or -1 if unknown.
        :rtype:  int
        :raises TransportError: If an error occurs while communicating with the
                                server.
        """
        if self._size == -1 and 'size' in self.features:
            if self._size_reply is None:
                self._size_reply = re.compile(r'^213 (\d+)[\n\r]*')

            self._connection.voidcmd('TYPE I')
            try:
                reply = self._connection.sendcmd('SIZE ' + self._name)
            except ftplib.error_perm as error:
                raise NotFoundError(error)
            match = self._size_reply.match(reply)
            self._size = int(match.group(1)) if match else -1
        return self._size

    @property
    def _connection(self):
        if self.__connection is None:
            self.__connection = ftplib.FTP(timeout=self._DEFAULT_TIMEOUT)
            try:
                self.__connection.connect(self._host, self._port)
                self.__connection.login(self._user, self._password)
            except socket.gaierror as error:
                raise ConnectionError(error)
            except ftplib.error_reply as error:
                raise AuthenticationError(error)
            except ftplib.all_errors + (socket.error,) as error:
                raise TransportError(error)

            try:
                self.__connection.cwd(self._path)
            except ftplib.error_reply as error:
                raise NotFoundError(error)
        return self.__connection

    def _do_get_content(self):
        try:
            self._connection.retrbinary('RETR ' + self._name, self._content.write)
        except (ftplib.Error, socket.error) as error:
            raise TransportError(error.message)


class HttpTransport(Transport):
    """
    An abstraction for retrieving resources, and their metadata, from HTTP
    servers.
    """
    def __init__(self, *args, **kwargs):
        """
        Create an instance of the HTTP transport mechanism.

        :param url: The URL of the resource to be obtained.
        :type  url: str
        :param user: The user name required to access the resource specified in
                     `url` (optional).
        :type  user: str
        :param password: The password required to access the resource specified
                         in `url` (optional).
        :type  password: str
        """
        super(HttpTransport, self).__init__(*args, **kwargs)
        self._client = httplib2.Http()
        self._client.add_credentials(self._user, self._password)
        self._metadata = None
        self._modification_date = None
        self._size = -1

    def get_modification_date(self):
        """
        Return the date and time of the last modification to this resource as
        reported by the remote source.

        :return: The modification date and time, or None if unknown.
        :rtype:  datetime | None
        """
        if self._modification_date is None:
            metadata = self._get_metadata()
            timestamp = parse_http_date_safe(metadata.get("last-modified"))
            if timestamp:
                self._modification_date = datetime.fromtimestamp(timestamp, utc)
        return self._modification_date

    def get_size(self):
        """
        Return the size of this resource as reported by the remote source.

        :return: The size (in bytes) of this resource, or -1 if unknown.
        :rtype:  int
        """
        if self._size == -1:
            metadata = self._get_metadata()
            self._size = int(metadata.get("content-length", -1))
        return self._size

    def _get_metadata(self):
        if self._metadata is None:
            self._metadata, _ = self._do_request("HEAD")
        return self._metadata

    def _do_request(self, method="GET"):
        try:
            response, content = self._client.request(self._url, method)
        except httplib2.ServerNotFoundError as error:
            raise NotFoundError(error)
        except (httplib.HTTPException, httplib2.HttpLib2Error, socket.error) as error:
            raise ConnectionError(error)

        if response == 401:
            raise AuthenticationError()
        elif 400 >= response < 500:
            raise NotFoundError()
        elif 500 >= response:
            raise ConnectionError()

        return response, content

    def _do_get_content(self):
        response, content = self._do_request()
        if response.status != 200:
            raise TransportError(response.reason)
        self._content.write(content)
