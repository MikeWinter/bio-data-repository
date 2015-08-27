"""
Defines the administrative representations of model classes defined in the
models subpackage.
"""

from django.contrib import admin

from .models import Category, Dataset, Tag

__all__ = []
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

admin.site.register(Category)
admin.site.register(Tag)


class DatasetAdmin(admin.ModelAdmin):
    """
    Administrative options for the Dataset model class.
    """
    prepopulated_fields = {"slug": ("name",)}

admin.site.register(Dataset, DatasetAdmin)
