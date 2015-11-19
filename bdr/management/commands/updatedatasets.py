"""
Specifies a command for updating datasets in the repository that are
out-of-date with respect to their remote data source.
"""

from django.core.management.base import NoArgsCommand

from ...models import Dataset

__all__ = ["Command"]
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


# noinspection PyAbstractClass
# The handle method is already implemented by the base class.
class Command(NoArgsCommand):
    """
    Updates datasets in the repository that are out-of-date with respect to
    their remote data source.
    """

    help = ("Queries the source associated with each dataset in the"
            " repository, updating any out-of-date files encountered.")
    """A short description of the command to be printed in help messages."""

    def handle_noargs(self, **options):
        """
        Iterate over datasets in the repository with remote data sources, and
        add new revisions for files that have been updated.

        :param options: Command-line arguments for this command.
        :type options: dict of str
        """
        for dataset in Dataset.objects.all():
            dataset.update()
