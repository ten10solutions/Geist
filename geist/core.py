from __future__ import division, absolute_import, print_function

import time
import logging
from hamcrest import has_length, greater_than_or_equal_to, less_than_or_equal_to
from hamcrest.core.string_description import tostring as describe_to_string
from .keyboard import KeyDown, KeyUp, KeyDownUp, keyboard_layout_factory


logger = logging.getLogger(__name__)


class NotFoundError(LookupError):
    """Raised when something couldn't be found
    """
    pass


class Location(object):
    def __init__(self, x, y, w=0, h=0, main_point_offset=None, image=None):
        self._x, self._y, self._w, self._h = x, y, w, h
        if main_point_offset is None:
            main_point_offset = (w // 2, h // 2)
        self._main_point_offset = main_point_offset
        self._mp_x_offset, self._mp_y_offset = main_point_offset
        self._image = image

    @property
    def image_region(self):
        if self._image is None:
            raise ValueError('Location does not have an image')
        if self.w < 1:
            raise ValueError('Location does not have a positive width')
        if self.h < 1:
            raise ValueError('Location does not have a positive height')
        return self._image[self.y:self.y + self.h, self.x:self.x + self.w]

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def w(self):
        return self._w

    @property
    def h(self):
        return self._h

    def find(self, gui):
        yield Location(self.x, self.y, self.w, self.h,
                       self.main_point_offset, gui.capture())

    @property
    def main_point_offset(self):
        return tuple(self._main_point_offset)

    @property
    def main_point(self):
        return (self.x + self._mp_x_offset, self.y + self._mp_y_offset)

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
        return "Location(x=%r, y=%r, w=%r, h=%r, main_point_offset=%r)" % (
            self.x,
            self.y,
            self.w,
            self.h,
            (self._mp_x_offset,  self._mp_y_offset))


class LocationList(list):
    def find(self, gui):
        for loc in self:
            yield next(loc.find(gui))


class _LazyGUIMethodSnapshot(object):
    def __init__(self, target, cached_methods=('capture',)):
        self._target = target
        self._cache = {}
        self._cached_methods = cached_methods

    def _get_cache_key(self, name, *args, **kwargs):
        return (name,
                tuple(args),
                frozenset((k,v) for k,v in kwargs.iteritems()))

    def __getattr__(self, name):
        if name in self._cached_methods:
            func = getattr(self._target, name)
            def cached_function(*args, **kwargs):
                key = self._get_cache_key(name, *args, **kwargs)
                if key in self._cache:
                    result = self._cache[key]
                else:
                    result = func(*args, **kwargs)
                    self._cache[key] = result
                return result
            return cached_function
        else:
            return getattr(self._target, name)


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

    def find_all(self, finder):
        return LocationList(finder.find(_LazyGUIMethodSnapshot(self)))

    def capture(self):
        return self._backend.capture()

    def wait_find_with_result_matcher(self, finder, matcher):
        start_t = time.time()
        while True:
            results = self.find_all(finder)
            if matcher.matches(results):
                return results
            if time.time() - start_t > self.config_finder_timeout:
                raise NotFoundError(
                    "Waited for results matching %s from %s. Last result %r" % (
                        describe_to_string(matcher),
                        finder,
                        results))

    def wait_find_n(self, n, finder):
        return self.wait_find_with_result_matcher(finder, has_length(n))

    def wait_find_one(self, finder):
        return self.wait_find_n(1, finder)[0]

    def click(self, finder):
        point = self.wait_find_one(finder).main_point
        with self._backend.actions_transaction() as actions:
            actions.add_move(point)
            actions.add_wait(self.config_mouse_move_wait)
            actions.add_button_down(1)
            actions.add_wait(self.config_mouse_button_wait)
            actions.add_button_up(1)
            actions.add_wait(self.config_mouse_button_wait)

    def double_click(self, finder):
        point = self.wait_find_one(finder).main_point
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
        to_x, to_y = (_from[0] + offset[0], _from[1] + offset[1])
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



class LocationFinderFilter(object):
    def __init__(self, filter_func, finder):
        self.filter_func = filter_func
        self.finder = finder

    def find(self, gui):
        for loc in self.finder.find(gui):
            if self.filter_func(loc):
                yield loc

    def __repr__(self):
        return '(Filter results of %r with %r)' % (
            self.finder,
            self.filter_func
        )
