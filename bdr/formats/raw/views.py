"""
This module defines classes for displaying raw type formats.
"""

import os.path

from django.http import StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.gzip import gzip_page
from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin

from ...views.formats import FormatDetailView
from ...models.base import Revision

__all__ = ["Record", "Reader", "Writer"]
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


class RawFormatDetailView(FormatDetailView):
    """
    This view indicates to the user that this format type cannot be modified.
    """

    template_name = "bdr/formats/raw/detail.html"


class RawRevisionExportView(SingleObjectMixin, View):
    """
    This view streams a compressed file to the client.

    File compression is performed on the fly.

    This class overrides the get method of the Django View class. For more
    information see
    https://docs.djangoproject.com/en/1.6/ref/class-based-views/base/#django.views.generic.base.View
    """

    model = Revision
    pk_url_kwarg = "rpk"

    @method_decorator(gzip_page)
    def get(self, *args, **kwargs):
        """
        Respond to a GET request by streaming the requested file to the client,
        compressing on-the-fly.

        :param args: The positional arguments extracted from the route.
        :param kwargs: The keyword argument extracted from the route.
        """
        revision = self.get_object()
        response = StreamingHttpResponse(revision.data, content_type="application/octet-stream")
        response["Content-Disposition"] = "attachment; filename={:s}".format(os.path.basename(revision.file.name))
        return response
