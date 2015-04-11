from django.forms import widgets
from django.utils.safestring import mark_safe


class AnnotatedNumberInput(widgets.NumberInput):
    def __init__(self, attrs=None, prefix=None, suffix=None):
        super(AnnotatedNumberInput, self).__init__(attrs)
        self._prefix = prefix
        self._suffix = suffix

    def render(self, name, value, attrs=None):
        html = super(AnnotatedNumberInput, self).render(name, value, attrs)
        if self._prefix:
            html = r'''<span class="input-group-addon">%s</span>
            %s''' % (self._prefix['text'], html)
        if self._suffix:
            html += r'''<span class="input-group-addon">%s</span>
            ''' % self._suffix['text']
        return mark_safe(r'''<div class="input-group">
            %s</div>''' % html)


class ComboTextInput(widgets.MultiWidget):
    def __init__(self, choices, default='', attrs=None):
        if attrs is None:
            attrs = {}
        attrs.update(datatype='combobox')
        self._choices = choices
        self._default = default
        super(ComboTextInput, self).__init__([widgets.Select(choices=self._choices), widgets.TextInput], attrs)

    def decompress(self, value):
        if value is None:
            return [self._default, '']
        if value == '':
            return ['None', '']
        for val, txt in self._choices:
            if value == val:
                return [value, '']
        return ['', value]

    def value_from_datadict(self, data, files, name):
        suggested, custom = super(ComboTextInput, self).value_from_datadict(data, files, name)
        value = suggested if suggested != '' else custom
        return value if value != 'None' else ''
