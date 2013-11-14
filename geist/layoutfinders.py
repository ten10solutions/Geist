from __future__ import division, absolute_import, print_function
from .core import Location


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


class LocationOperatorFinderBuilder(object):
    def __init__(self, operation):
        self.operation = operation

    def __and__(self, other):
        return LocationOperatorFinderBuilder(
            lambda a, b: self.operation(a, b) and other.operation(a, b)
        )

    def __or__(self, other):
        return LocationOperatorFinderBuilder(
            lambda a, b: self.operation(a, b) or other.operation(a, b)
        )

    def __call__(self, a_finder, b_finder):
        return LocationOperatorFinder(self.operation, a_finder, b_finder)



def below_op(a, b):
    return b.y >= (a.y + a.h)


def above_op(a, b):
    return b.y + b.h <= a.y


def left_of_op(a, b):
    return b.x + b.w >= a.x


def right_of_op(a, b):
    return b.x <= (a.x + a.w)


def row_aligned_op(a, b):
    return a.y <= b.center[1] <= (a.y + a.h)


def column_aligned_op(a, b):
    return a.x <= b.center[0] <= (a.x + a.w)


class MaxDistanceOp(object):
    def __init__(self, max_distance):
        self.max_distance = max_distance

    def __call__(self, a, b):
        x1, y1 = a.center
        x2, y2 = b.center
        return (((x1 - x2) ** 2) + ((y1 - y2) ** 2)) ** 0.5 <= self.max_distance


def intersects_op(a, b):
    return not (
        (b.x > (a.x + a.w)) |
        (b.x + b.w < a.x) |
        (b.y > (a.y + a.h)) |
        (b.y + b.h < a.y)
    )


below = LocationOperatorFinderBuilder(below_op)
above = LocationOperatorFinderBuilder(above_op)
left_of = LocationOperatorFinderBuilder(left_of_op)
right_of = LocationOperatorFinderBuilder(right_of_op)
row_aligned = LocationOperatorFinderBuilder(row_aligned_op)
column_aligned = LocationOperatorFinderBuilder(column_aligned_op)
intersects = LocationOperatorFinderBuilder(intersects_op)


class OffsetFromMainPointFinder(object):
    def __init__(self, base_finder, x_offset=0, y_offset=0):
        self.base_finder = base_finder
        self.x_offset = x_offset
        self.y_offset = y_offset


    def find(self, gui):
        for location in self.base_finder.find(gui):
            x, y = location.main_point
            yield Location(x + self.x_offset, y + self.y_offset)
