"""
Basic views for the Biological Data Repository Web application.

The following public classes are defined herein:
    AboutView: Displays a description of the motivation for the application.
    LegalView: Displays copyright, warranty and other legal information about
               the application.
"""

from django.views.generic import TemplateView

__all__ = ["AboutView", "LegalView"]
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


class AboutView(TemplateView):
    """
    Displays a description of the motivation for the application.

    Extends the django.views.generic.TemplateView class, overriding the
    template_name property.
    """

    template_name = "bdr/about.html"


class LegalView(TemplateView):
    """
    Displays copyright, warranty and other legal information about the
    application.

    Extends the django.views.generic.TemplateView class, overriding the
    template_name property.
    """

    template_name = "bdr/legal.html"
