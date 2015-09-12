"""
Basic views for the Biological Data Repository Web application.

The following public classes are defined herein:

    AboutView
        Displays a description of the motivation for the application.
    HomeView
        Displays the application home page.
    LegalView
        Displays copyright, warranty and other legal information about the
        application.

A single view function is exported:

    search_script
        Returns a script for use with repository search forms.

The following mixin is also provided:

    SearchableViewMixin
        Injects a search form into the context object for a template.
"""

from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.views.generic import ListView, TemplateView

from ..forms import SearchForm
from ..models import Category, Dataset, Update

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


@cache_page(60 * 10)
def search_script(request):
    """
    Return a script that configures type-ahead functionality during searches.

    :param request: The HTTP request for this script.
    :type request: django.http.HttpRequest
    :return: The script content response.
    :rtype: django.http.HttpResponse
    """
    return render(request, "bdr/search.js", content_type="text/javascript")


class SearchableViewMixin(object):
    """
    Injects a search form into the context object for a template.

    This mixin is intended to be used with a class that also inherits from
    either `django.views.generic.TemplateView` or
    `django.views.generic.FormView`.

    It is the responsibility of the subtype to handle the form submission in
    some sensible fashion. This is most likely to be setting the form action to
    point to a form view.
    """

    search_form_class = SearchForm
    """The form type used to create the search form."""
    search_form_key = "search_form"
    """The key name with which the form can be found in the context object."""

    def get_context_data(self, **kwargs):
        """
        Provides a search form to the context dictionary used in template-based
        views. The search form is added under the key specified by the
        `search_form_key` property (default: "search_form").

        :param kwargs: A mapping of data available for use in templates.
        :type kwargs: dict
        :return: A dictionary of key/value pairs.
        :rtype: dict
        """
        # noinspection PyUnresolvedReferences
        # The get_context_data method is provided by
        # `django.views.generic.base.ContextMixin`
        context = super(SearchableViewMixin, self).get_context_data(**kwargs)
        context.update({
            self.search_form_key: self.search_form_class()
        })
        return context


class AboutView(SearchableViewMixin, TemplateView):
    """
    Displays a description of the motivation for the application.

    Extends the django.views.generic.TemplateView class, overriding the
    template_name property.
    """

    template_name = "bdr/about.html"
    """Defines the template file used to present the view."""


class LegalView(SearchableViewMixin, TemplateView):
    """
    Displays copyright, warranty and other legal information about the
    application.

    Extends the django.views.generic.TemplateView class, overriding the
    template_name property.
    """

    template_name = "bdr/legal.html"
    """Defines the template file used to present the view."""


class HomeView(SearchableViewMixin, ListView):
    """
    This view displays a list of recently updated files, and a categorised list
    of the datasets stored in the repository.

    This class extends the get_context_data method of the Django TemplateView
    class from which it inherits. For more information, see
    https://docs.djangoproject.com/en/1.6/ref/class-based-views/base/
    """

    model = Update
    """The class of domain model listed by this view."""
    template_name = "bdr/home.html"
    """Defines the template file used to present the view."""

    def get_context_data(self, **kwargs):
        """
        Set up and return variables for use in the template for this view.

        :param kwargs: A mapping of data available for use in templates.
        :type kwargs: dict
        :return: A dictionary of key/value pairs.
        :rtype: dict
        """
        context = super(HomeView, self).get_context_data(**kwargs)
        context.update({
            "category_list": Category.objects.exclude(dataset__isnull=True),
            "dataset_list": Dataset.objects.filter(categories__isnull=True),
        })
        return context
