from __future__ import division, absolute_import, print_function

import time
import logging
from hamcrest import (
    has_length, greater_than_or_equal_to, less_than_or_equal_to)
from hamcrest.core.string_description import tostring as describe_to_string
import numpy
from .keyboard import KeyDown, KeyUp, KeyDownUp, keyboard_layout_factory


logger = logging.getLogger(__name__)


class NotFoundError(LookupError):
    """Raised when something couldn't be found
    """
    pass


class Location(object):
    def __init__(self, rel_x, rel_y, w=0, h=0, main_point_offset=None,
                 parent=None, image=None):
        if rel_x < 0:
            raise ValueError('rel_x must be >= 0')
        if rel_y < 0:
            raise ValueError('rel_y must be >= 0')
        if parent is not None and w > parent.w:
            raise ValueError('w must be <= parent.w or parent must be None')
        if parent is not None and h > parent.h:
            raise ValueError('h must be <= parent.h or parent must be None')

        self._rel_x, self._rel_y, self._w, self._h = rel_x, rel_y, w, h
        if main_point_offset is None:
            self._main_point_offset = (w // 2, h // 2)
        else:
            self._main_point_offset = tuple(main_point_offset)
        self._parent = parent
        if image is not None:
            ih, iw = image.shape[:2]
            if ih != h or iw != w:
                raise AssertionError('image width and height should be the '
                                     'same as the locations')
        self._image = image

    @property
    def parent(self):
        return self._parent

    @property
    def image(self):
        if self.w < 1 or self.h < 1:
            raise AttributeError(
                "Can not get image from Locations with zero width or height"
            )
        if self.parent is not None:
            return self.parent.image[self.rel_y:self.rel_y + self.h,
                                     self.rel_x:self.rel_x + self.w]
        if self._image is not None:
            return self._image
        else:
            return numpy.zeros((self.h, self.w, 3), dtype=numpy.uint8)

    @property
    def rel_x(self):
        return self._rel_x

    @property
    def rel_y(self):
        return self._rel_y

    @property
    def x(self):
        if self.parent is None:
            return self.rel_x
        else:
            return self.rel_x + self.parent.x

    @property
    def y(self):
        if self.parent is None:
            return self.rel_y
        else:
            return self.rel_y + self.parent.y

    @property
    def w(self):
        return self._w

    @property
    def h(self):
        return self._h

    def find(self, in_location):
        if (
            self.rel_x + self.w <= in_location.x + in_location.w
        ) and (
            self.rel_y + self.h <= in_location.y + in_location.h
        ):
            yield self.copy(parent=in_location)

    def copy(self, **update_attrs):
        attrs = dict(
            (attr, getattr(self, attr)) for attr in
            ['rel_x', 'rel_y', 'w', 'h', 'main_point_offset', 'parent']
        )
        attrs['image'] = self._image
        attrs.update(update_attrs)
        return Location(**attrs)

    @property
    def main_point_offset(self):
        return self._main_point_offset

    @property
    def main_point(self):
        return (
            self.x + self._main_point_offset[0],
            self.y + self._main_point_offset[1]
        )

    @property
    def center(self):
        return (self.x + (self.w // 2), self.y + (self.h // 2))

    @property
    def rect(self):
        return (self.x, self.y, self.w, self.h)

    @property
    def area(self):
        return self.w * self.h

    def __repr__(self):
        return "Location(x=%r, y=%r, w=%r, h=%r, main_point_offset=%r, parent=%r)" % (
            self.x,
            self.y,
            self.w,
            self.h,
            self._main_point_offset,
            self.parent,
            )

    def __eq__(self, other):
        if self.parent != other.parent:
            return False
        if ((self.rel_x, self.rel_y, self.w, self.h) !=
            (other.rel_x, other.rel_y, other.w, other.h)):
            return False
        if self.main_point_offset != other.main_point_offset:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)


class LocationList(list):
    def find(self, in_location):
        for loc in self:
            try:
                yield next(loc.find(in_location))
            except StopIteration:
                pass


class GUI(object):
    def __init__(self, backend, keyboard_layout=None):
        self._backend = backend
        if keyboard_layout is None:
            keyboard_layout = keyboard_layout_factory('default')
        self._keyboard_layout = keyboard_layout
        self.config_finder_timeout = 30
        self.config_mouse_move_wait = 0.01
        self.config_mouse_button_wait = 0.01
        self.config_key_down_wait = 0.01
        self.config_key_up_wait = 0.01

    def _find_all_gen(self, finder):
        for in_location in self.capture_locations():
            for loc in finder.find(in_location):
                if (in_location.x, in_location.y) != (0, 0):
                    loc = loc.copy(
                        x=loc.x + in_location.x,
                        y=loc.y + in_location.y
                    )
                yield loc

    def find_all(self, finder):
        return LocationList(self._find_all_gen(finder))

    def capture_locations(self):
        return LocationList(self._backend.capture_locations())

    def wait_find_with_result_matcher(self, finder, matcher):
        start_t = time.time()
        while True:
            results = self.find_all(finder)
            if matcher.matches(results):
                return results
            if time.time() - start_t > self.config_finder_timeout:
                raise NotFoundError("Waited for results matching %s from %s."
                                    "Last result %r" % (
                                        describe_to_string(matcher),
                                        finder,
                                        results))

    def wait_find_n(self, n, finder):
        return self.wait_find_with_result_matcher(finder, has_length(n))

    def wait_find_one(self, finder):
        return self.wait_find_n(1, finder)[0]

    def click(self, finder):
        point = self.wait_find_one(finder).main_point
        # problem is numpy 32 bit ints rather than normal...
        point = (int(point[0]), int(point[1]))
        with self._backend.actions_transaction() as actions:
            actions.add_move(point)
            actions.add_wait(self.config_mouse_move_wait)
            actions.add_button_down(1)
            actions.add_wait(self.config_mouse_button_wait)
            actions.add_button_up(1)
            actions.add_wait(self.config_mouse_button_wait)

    def double_click(self, finder):
        point = self.wait_find_one(finder).main_point
        point = (int(point[0]), int(point[1]))
        with self._backend.actions_transaction() as actions:
            actions.add_move(point)
            actions.add_wait(self.config_mouse_move_wait)
            actions.add_button_down(1)
            actions.add_wait(self.config_mouse_button_wait)
            actions.add_button_up(1)
            actions.add_wait(self.config_mouse_button_wait)
            actions.add_button_down(1)
            actions.add_wait(self.config_mouse_button_wait)
            actions.add_button_up(1)
            actions.add_wait(self.config_mouse_button_wait)

    def context_click(self, finder):
        point = self.wait_find_one(finder).main_point
        point = (int(point[0]), int(point[1]))
        with self._backend.actions_transaction() as actions:
            actions.add_move(point)
            actions.add_wait(self.config_mouse_move_wait)
            actions.add_button_down(3)
            actions.add_wait(self.config_mouse_button_wait)
            actions.add_button_up(3)
            actions.add_wait(self.config_mouse_button_wait)

    def key_presses(self, *text_or_keys):
        key_actions = []
        for text_or_key in text_or_keys:
            if isinstance(text_or_key, (KeyDown, KeyUp)):
                key_actions += [text_or_key]
            elif isinstance(text_or_key, KeyDownUp):
                key_actions += [
                    KeyDown(str(text_or_key)),
                    KeyUp(str(text_or_key))
                ]
            else:
                for c in text_or_key:
                    key_actions += self._keyboard_layout(c)
        with self._backend.actions_transaction() as actions:
            for key_action in key_actions:
                if isinstance(key_action, KeyDown):
                    actions.add_key_down(str(key_action))
                    actions.add_wait(self.config_key_down_wait)
                elif isinstance(key_action, KeyUp):
                    actions.add_key_up(str(key_action))
                    actions.add_wait(self.config_key_up_wait)
                else:
                    raise ValueError('Key action must be a KeyUp or KeyDown')

    def drag(self, from_finder, to_finder):
        _from = self.wait_find_one(from_finder).main_point
        to = self.wait_find_one(to_finder).main_point
        with self._backend.actions_transaction() as actions:
            actions.add_move(_from)
            actions.add_wait(self.config_mouse_move_wait)
            actions.add_button_down(1)
            actions.add_wait(self.config_mouse_button_wait)
            actions.add_move(to)
            actions.add_wait(self.config_mouse_move_wait)
            actions.add_button_up(1)
            actions.add_wait(self.config_mouse_button_wait)

    def drag_relative(self, from_finder, offset):
        from_x, from_y = self.wait_find_one(from_finder)
        to_x, to_y = (from_x + offset[0], from_y + offset[1])
        self.drag(
            Location(from_x, from_y),
            Location(to_x, to_y)
        )

    def move(self, finder):
        point = self.wait_find_one(finder).main_point
        with self._backend.actions_transaction() as actions:
            actions.add_move(point)
            actions.add_wait(self.config_mouse_move_wait)

    def exists(self, finder):
        return True if self.find_all(finder) else False

    def exists_within_timeout(self, finder):
        try:
            self.wait_find_with_result_matcher(
                finder,
                has_length(greater_than_or_equal_to(1))
            )
            return True
        except NotFoundError:
            return False

    def does_not_exist_within_timeout(self, finder):
        try:
            self.wait_find_with_result_matcher(
                finder,
                has_length(less_than_or_equal_to(0))
            )
            return True
        except NotFoundError:
            return False
