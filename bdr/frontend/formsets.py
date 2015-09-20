from django.core.exceptions import ValidationError
from django.forms.formsets import TOTAL_FORM_COUNT
from django.forms.models import inlineformset_factory, modelformset_factory

from bdr.frontend import forms, models


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
