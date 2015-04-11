from django.core.exceptions import ValidationError
from django.forms.formsets import TOTAL_FORM_COUNT
from django.forms.models import inlineformset_factory, formset_factory, modelformset_factory

from bdr.frontend import forms, models


class ArchiveMemberSelectionFormSet(formset_factory(forms.ArchiveMemberForm, extra=0)):
    def clean(self):
        selected = [form for form in self.forms
                    if not self._should_delete_form(form) and form.cleaned_data.get('selected', False)]
        if len(selected) == 0:
            raise ValidationError("No files selected.")


class FileListFormSet(modelformset_factory(models.File, forms.FileEditForm, extra=0)):
    def __init__(self, *args, **kwargs):
        # kwargs.update(queryset=self.model.objects.none())
        super(FileListFormSet, self).__init__(*args, **kwargs)


class FormatFieldInlineFormSet(inlineformset_factory(models.Format, models.FormatField, forms.FormatFieldForm)):
    def __init__(self, *args, **kwargs):
        super(FormatFieldInlineFormSet, self).__init__(*args, **kwargs)
        self.data = self.data.copy()

    def add_extra_form(self):
        field_name = self.add_prefix(TOTAL_FORM_COUNT)
        self.data[field_name] = int(self.data[field_name]) + 1


class FieldSelectionListFormSet(modelformset_factory(models.FormatField, forms.FormatFieldSelectionForm, extra=0)):
    def clean(self):
        if len(self.forms) > 0 and len(self.get_selected()) == 0:
            raise ValidationError("At least one field must be selected.")
        return super(FieldSelectionListFormSet, self).clean()

    def get_selected(self):
        return [item for item in self.cleaned_data if item['selected']]
