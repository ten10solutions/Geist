from __future__ import division, absolute_import, print_function
from .core import Location
from itertools import groupby


class FinderInFinder(object):
    def __init__(self, finder, in_finder):
        self._finder = finder
        self._in_finder = in_finder

    def find(self, in_location):
        for location in self._in_finder.find(in_location):
            for sub_location in self._finder.find(location):
                if (location.x, location.y) != (0, 0):
                    sub_location = sub_location.copy(
                        x=sub_location.x + location.x,
                        y=sub_location.y + location.y
                    )
                yield sub_location

    def __repr__(self):
        return "match things found by [%r] in locations found by [%r]" % (
            self._finder,
            self._in_finder,
        )


class LocationOperatorFinder(object):
    def __init__(self, a_finder, operator, b_finder):
        self._operator = operator
        self._a_finder = a_finder
        self._b_finder = b_finder

    def find(self, in_location):
        b_locations = list(self._b_finder.find(in_location))
        for a_location in self._a_finder.find(in_location):
            for b_location in b_locations:
                if self._operator(a_location, b_location):
                    yield a_location
                    break

    def __repr__(self):
        return "Things found by [%r] are [%r] thing found by [%r]" % (
            self._a_finder,
            self._operator,
            self._b_finder
        )


class Operation(object):
    def __and__(self, other):
        return _and(self, other)

    def __or__(self, other):
        return _or(self, other)

    def __invert__(self):
        return _invert(self)


class _and(Operation):
    def __init__(self, a_op, b_op):
        self.a_op, self.b_op = a_op, b_op

    def __call__(self, a, b):
        return self.a_op(a, b) and self.b_op(a, b)

    def __repr__(self):
        return "%r and %r" % (self.a_op, self.b_op)


class _or(Operation):
    def __init__(self, a_op, b_op):
        self.a_op, self.b_op = a_op, b_op

    def __call__(self, a, b):
        return self.a_op(a, b) or self.b_op(a, b)

    def __repr__(self):
        return "%r or %r" % (self.a_op, self.b_op)


class _invert(Operation):
    def __init__(self, a_op):
        self.a_op = a_op

    def __call__(self, a, b):
        return self.a_op(a, b) ^ True

    def __repr__(self):
        return "invert %r" % (self.a_op)


class _SimpleOperation(Operation):
    def __init__(self, op_func, doc):
        self.op_func, self.doc = op_func, doc

    def __call__(self, a, b):
        return self.op_func(a, b)

    def __repr__(self):
        return self.doc

below = _SimpleOperation(lambda a, b: b.y + b.h <= a.y, "is below")
above = _SimpleOperation(lambda a, b: b.y >= (a.y + a.h), "is above")
left_of = _SimpleOperation(lambda a, b: b.x + b.w >= a.x, "is left of")
right_of = _SimpleOperation(lambda a, b: b.x <= (a.x + a.w), "is right of")


class max_horizontal_separation(Operation):
    def __init__(self, max_sep):
        self.max_sep = max_sep

    def __call__(self, a, b):
        if b.x > a.x + a.w:
            sep = b.x - (a.x + a.w)
        elif a.x > (b.x + b.w):
            sep = a.x - (b.x + b.w)
        else:
            sep = 0
        return sep <= self.max_sep

    def __repr__(self):
        return "has horizontal seperation less than or equal to %r" % (
            self.max_sep,
        )


class max_vertical_separation(Operation):
    def __init__(self, max_sep):
        self.max_sep = max_sep

    def __call__(self, a, b):
        if b.y > a.y + a.h:
            sep = b.y - (a.y + a.h)
        elif a.y > (b.y + b.h):
            sep = a.y - (b.y + b.h)
        else:
            sep = 0
        return sep <= self.max_sep

    def __repr__(self):
        return "has vertical seperation less than or equal to %r" % (
            self.max_sep,
        )


row_aligned = max_vertical_separation(0)
column_aligned = max_horizontal_separation(0)
intersects = row_aligned & column_aligned
not_intersects = ~intersects


class MergeLocationsFinderFilter(object):
    def __init__(self, op, finder):
        self.op = op
        self.finder = finder

    def find(self, in_location):
        number_grouped_locations = [[num, loc] for num, loc in
                                    enumerate(self.finder.find(in_location))]
        for group1 in number_grouped_locations:
            groups = [group for group in number_grouped_locations if
                      self.op(group1[1], group[1])]
            groups.append(group1)
            num_max = max(i[0] for i in groups)
            for group in groups:
                group[0] = num_max
        for num, group in groupby(
            sorted(number_grouped_locations),
            lambda x: x[0]
        ):
            locations = [i[1] for i in group]
            image = locations[0]._image
            x = min(loc.x for loc in locations)
            y = min(loc.y for loc in locations)
            w = max(loc.x + loc.w for loc in locations) - x
            h = max(loc.y + loc.h for loc in locations) - y
            yield Location(x, y, w, h, parent=in_location)

    def __repr__(self):
        return ("Find all with %r then merge results when the following is "
                "True: %r") % (self.finder, self.op)
