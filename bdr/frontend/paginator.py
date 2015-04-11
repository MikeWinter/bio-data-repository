from django.core import paginator as base


class Paginator(base.Paginator):
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, adjacent_pages=2):
        self.adjacent_pages = adjacent_pages
        super(Paginator, self).__init__(object_list, per_page, orphans, allow_empty_first_page)

    def _get_page(self, *args, **kwargs):
        """Returns an instance of a single page."""
        return Page(*args, **kwargs)


class Page(base.Page):
    def __init__(self, object_list, number, paginator):
        super(Page, self).__init__(object_list, number, paginator)

    def _get_active_range(self):
        if self._is_small_range():
            return range(1, self.paginator.num_pages + 1)
        elif self._in_leading_range() or self._in_trailing_range():
            return []
        lower = max(self.number - self.paginator.adjacent_pages, 1)
        upper = min(self.number + self.paginator.adjacent_pages, self.paginator.num_pages)
        return range(lower, upper + 1)
    active_range = property(_get_active_range)

    def _get_leading_range(self):
        if self._is_small_range():
            return []
        upper = self.paginator.adjacent_pages
        if self.in_leading_range():
            upper = upper + self.number
        return range(1, upper + 1)
    leading_range = property(_get_leading_range)

    def _get_trailing_range(self):
        if self._is_small_range():
            return []
        if self.in_trailing_range():
            lower = self.number
        else:
            lower = self.paginator.num_pages + 1
        return range(lower - self.paginator.adjacent_pages, self.paginator.num_pages + 1)
    trailing_range = property(_get_trailing_range)

    def in_leading_range(self):
        return self._in_leading_range() and not self._is_small_range()

    def in_trailing_range(self):
        return self._in_trailing_range() and not self._is_small_range()

    def _in_leading_range(self):
        return self.number <= (self.paginator.adjacent_pages * 2 + 1)

    def _in_trailing_range(self):
        return self.number >= (self.paginator.num_pages - self.paginator.adjacent_pages * 2)

    def _is_small_range(self):
        return self.paginator.num_pages <= (self.paginator.adjacent_pages * 3 + 1)
