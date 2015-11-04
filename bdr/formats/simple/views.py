try:
    import cPickle as pickle
except ImportError:
    import pickle

from django.forms.formsets import DELETION_FIELD_NAME
from django.views.generic.edit import ModelFormMixin

from ...forms import SimpleFormatForm
from ...forms.sets import SimpleFormatFieldFormSet
from ...views.formats import FormatDetailView, FormatCreateView, FormatEditView

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


class SimpleFormatDetailView(FormatDetailView):
    """
    This view displays the details of a format, including a list of its fields.
    """

    template_name = "bdr/formats/simple/simple_detail.html"

    def get_context_data(self, **kwargs):
        """
        Return the template context for this view.

        This method returns a dictionary containing variables for the rendered
        view. Available template context variables are:

         * ``fields`` - a list of fields used by this instance
         * ``format`` - the format model

        :param kwargs: A mapping of extra data available for use in templates.
        :type kwargs: dict of str
        :return: A dictionary of template variables and values.
        :rtype: dict of str
        """
        settings = pickle.loads(str(self.object.metadata))
        context = super(SimpleFormatDetailView, self).get_context_data(**kwargs)
        context["fields"] = settings["fields"]
        return context


class SimpleFormatCreateView(FormatCreateView):
    """Used to create a new instance of the simple format type."""

    form_class = SimpleFormatForm
    template_name = "bdr/formats/simple/simple_create.html"

    def __init__(self, **kwargs):
        super(SimpleFormatCreateView, self).__init__(**kwargs)
        self._fieldset = None

    def get(self, request, *args, **kwargs):
        self._fieldset = SimpleFormatFieldFormSet()
        return super(SimpleFormatCreateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self._fieldset = SimpleFormatFieldFormSet(data=request.POST)
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if request.POST.get("operation") == "add":
            self._fieldset.add_extra_form()
            return self.render_to_response(self.get_context_data(form=form))

        if form.is_valid() and self._fieldset.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(SimpleFormatCreateView, self).get_context_data(**kwargs)
        context["formset"] = self._fieldset
        return context

    def form_valid(self, form):
        fields = [{"name": field["name"], "is_key": field["is_key"]}
                  for field in self._fieldset.cleaned_data if field and not field[DELETION_FIELD_NAME]]
        settings = dict(delimiter=form.cleaned_data["separator"], quotechar=form.cleaned_data["quote"],
                        comment=form.cleaned_data["comment"], fields=fields)
        self.object = form.save(commit=False)
        self.object.entry_point_name = "simple"
        self.object.metadata = pickle.dumps(settings, pickle.HIGHEST_PROTOCOL)
        self.object.save()
        return super(ModelFormMixin, self).form_valid(form)


class SimpleFormatEditView(FormatEditView):
    """Used to edit an existing instance of the simple format type."""

    form_class = SimpleFormatForm
    template_name = "bdr/formats/simple/simple_edit.html"

    def __init__(self, **kwargs):
        super(SimpleFormatEditView, self).__init__(**kwargs)
        self._fieldset = None

    def get(self, request, *args, **kwargs):
        object = self.get_object()
        settings = pickle.loads(str(object.metadata))
        self._fieldset = SimpleFormatFieldFormSet(initial=settings["fields"])
        self._fieldset.extra = 1
        return super(SimpleFormatEditView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self._fieldset = SimpleFormatFieldFormSet(data=request.POST)
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if request.POST.get('operation') == 'add':
            self._fieldset.add_extra_form()
            return self.render_to_response(self.get_context_data(form=form))

        if form.is_valid() and self._fieldset.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(SimpleFormatEditView, self).get_context_data(**kwargs)
        context['formset'] = self._fieldset
        return context

    def get_initial(self):
        settings = pickle.loads(str(self.object.metadata))
        return dict(separator=settings["separator"], quote=settings["quote"], comment=settings["comment"])

    def form_valid(self, form):
        fields = [{"name": field["name"], "is_key": field["is_key"]}
                  for field in self._fieldset.cleaned_data if field and not field[DELETION_FIELD_NAME]]
        settings = dict(separator=form.cleaned_data["separator"], quote=form.cleaned_data["quote"],
                        comment=form.cleaned_data["comment"], fields=fields)
        self.object = form.save(commit=False)
        self.object.entry_point_name = "simple"
        self.object.metadata = pickle.dumps(settings, pickle.HIGHEST_PROTOCOL)
        self.object.save()
        return super(ModelFormMixin, self).form_valid(form)
