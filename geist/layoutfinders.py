from __future__ import division, absolute_import, print_function
from .core import Location
from itertools import groupby


class LocationOperatorFinder(object):
    def __init__(self, operator, a_finder, b_finder):
        self._operator = operator
        self._a_finder = a_finder
        self._b_finder = b_finder

    def find(self, gui):
        a_locations = list(self._a_finder.find(gui))
        for b_location in self._b_finder.find(gui):
            for a_location in a_locations:
                if self._operator(a_location, b_location):
                    yield b_location
                    break

    def __repr__(self):
        return "A=%r, B=%r: %r" % (
            self._a_finder,
            self._b_finder,
            self._operator
        )


class Operation(object):
    def __and__(self, other):
        return _and(self, other)

    def __or__(self, other):
        return _or(self, other)


class _and(Operation):
    def __init__(self, a_op, b_op):
        self.a_op, self.b_op = a_op, b_op

    def __call__(self, a, b):
        return self.a_op(a, b) and self.b_op(a, b)

    def __repr__(self):
        return "(%r and %r)" % (self.a_op, self.b_op)


class _or(Operation):
    def __init__(self, a_op, b_op):
        self.a_op, self.b_op = a_op, b_op

    def __call__(self, a, b):
        return self.a_op(a, b) or self.b_op(a, b)

    def __repr__(self):
        return "(%r or %r)" % (self.a_op, self.b_op)

class _SimpleOperation(Operation):
    def __init__(self, op_func, doc):
        self.op_func, self.doc = op_func, doc

    def __call__(self, a, b):
        return self.op_func(a, b)

    def __repr__(self):
        return self.doc

below = _SimpleOperation(
    lambda a, b: b.y + b.h <= a.y,
    "A is below all of B vertically"
)
above = _SimpleOperation(
    lambda a, b: b.y >= (a.y + a.h),
    "A is above all of B vertically"
)
left_of = _SimpleOperation(
    lambda a, b: b.x + b.w >= a.x,
    "A is left of B"
)
right_of = _SimpleOperation(
    lambda a, b: b.x <= (a.x + a.w),
    "A is right of B"
)


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
        return "A to B max horizontal seperation is less than or equal to %r" % (
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
        return "A to B max vertical seperation less than or equal to %r" % (
            self.max_sep,
        )


row_aligned = max_horizontal_separation(0)
column_aligned = max_vertical_separation(0)
intersects = row_aligned & column_aligned


class MergeLocationsFinderFilter(object):
    def __init__(self, op, finder):
        self.op = op
        self.finder = finder

    def find(self, gui):
        number_grouped_locations = [[num, loc] for num, loc in
                                    enumerate(self.finder.find(gui))]
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
            yield Location(x, y, w, h, image=image)

    def __repr__(self):
        return ("Find all with %r then merge results when the following is "
                "True: %r") % (
            self.finder,
            self.op
        )






