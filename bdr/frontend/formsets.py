from django.core.exceptions import ValidationError
from django.forms.models import modelformset_factory

from bdr.frontend import forms, models


class FieldSelectionListFormSet(modelformset_factory(models.FormatField, forms.FormatFieldSelectionForm, extra=0)):
    def clean(self):
        if len(self.forms) > 0 and len(self.get_selected()) == 0:
            raise ValidationError("At least one field must be selected.")
        return super(FieldSelectionListFormSet, self).clean()

    def get_selected(self):
        return [item for item in self.cleaned_data if item['selected']]
