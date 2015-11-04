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


