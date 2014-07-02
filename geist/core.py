from __future__ import division, absolute_import, print_function

import time
import logging
from hamcrest import (
    has_length, greater_than_or_equal_to, less_than_or_equal_to)
from hamcrest.core.string_description import tostring as describe_to_string
from .keyboard import KeyDown, KeyUp, KeyDownUp, keyboard_layout_factory
from .finders import LocationList, Location


logger = logging.getLogger(__name__)


class NotFoundError(LookupError):
    """Raised when something couldn't be found
    """
    pass


class _GuiMergedOptions(object):
    def __init__(self, base, overrides):
        self._options = dict(base)
        self._options.update(overrides)

    def __getattr__(self, item):
        try:
            return self._options[item]
        except KeyError:
            raise NameError(item)


class _GuiOptionsHelper(object):
    def __init__(self, text, options):
        self._method_allowed = set()
        constructor_allowed = set()
        defaults = {}
        for line in text.splitlines():
            if line.startswith('        -') or line.startswith('        *'):
                _type, opt_name, _, default_text = line.split()[:4]
                default_text = default_text.replace(']', '')
                default_value = eval(default_text)
                defaults[opt_name] = default_value
                if _type == '*':
                    constructor_allowed.add(opt_name)
                self._method_allowed.add(opt_name)
        for key in options:
            if key not in constructor_allowed:
                raise ValueError('%s is not a valid option' % (key,))
        self._base_options = dict(defaults)
        self._base_options.update(options)

    def merge(self, options):
        for key in options:
            if key not in self._method_allowed:
                raise ValueError('%s is not a valid option' % (key,))
        return _GuiMergedOptions(self._base_options, options)

    def __getattr__(self, item):
        try:
            return self._base_options[item]
        except KeyError:
            raise NameError(item)


class GUI(object):
    """A high level facade combining finders and backends.

    The following keyword options are supported on the constructor and methods
    which take options:
        * timeout [default 30 seconds]
            The retry time-out used when trying to find things or wait for
            changes.
        * mouse_move_increment [default 50 pixels]
            The distance in pixels the mouse will move at once when
            mouse_warping is False, smaller values may make make applications
            behave "correctly".
        * mouse_move_wait [default 0.005 seconds]
            The wait time after the mouse is moved on the backend.
            Note: if mouse_warping is False total time to take actions may be
            [(distance_to_move / mouse_move_increment) * mouse_move_wait] which
            may be sigificant.
        * mouse_button_down_wait [default 0.01 seconds]
            The wait time after pressing a mouse button.
        * mouse_button_up_wait [default 0 seconds]
            The wait time after releasing a mouse button.
        * mouse_warping [default True]
            If false the mouse is moved incrementally except when dragging
            which is controlled by mouse_warp_dragging.
        * mouse_warp_dragging  [default False]
            If false the mouse is moved incrementally when dragging.
        * key_down_wait [default 0.01 seconds]
            The wait time after pressing a key.
        * key_up_wait [default 0.01 seconds]
            The wait time after releasing a key.

    The following additional keyword options are supported on methods which
    take options:
        - wait_for_image_change_pre_action [default False]
            After doing a pre action move wait for the image under the found
            location to change before doing the action (click etc.)
        - wait_for_image_change_post_action [default False]
            After doing a doing an action (click etc.) wait for the image
            under the found location to change.
    """

    def __init__(self, backend, keyboard_layout=None, **options):
        self._opts = _GuiOptionsHelper(GUI.__doc__, options)
        self._backend = backend
        if keyboard_layout is None:
            keyboard_layout = keyboard_layout_factory('default')
        self._keyboard_layout = keyboard_layout

    def _find_all_gen(self, finder):
        for in_location in self.capture_locations():
            for loc in finder.find(in_location):
                if (in_location.x, in_location.y) != (0, 0):
                    loc = loc.copy(
                        x=loc.x + in_location.x,
                        y=loc.y + in_location.y
                    )
                yield loc

    def _wait_for_image_change(self, location, merged_opts):
        start_time = time.time()
        while True:
            updated_location = next(self._find_all_gen(location))
            if not location.equals_considering_only_image(updated_location):
                return
            if time.time() - start_time > merged_opts.timeout:
                raise NotFoundError("Image in %r didn't change" % (location,))

    def _move(self, actions, to_point, merged_opts):
        if merged_opts.mouse_warping:
            actions.add_move(to_point)
            if merged_opts.mouse_move_wait != 0:
                actions.add_wait(merged_opts.mouse_move_wait)
        else:
            from_point = self._backend.cursor_position()
            self._incremental_move(actions, from_point, to_point, merged_opts)

    def _button_click(self, actions, button, merged_opts):
        actions.add_button_down(button)
        if merged_opts.mouse_button_down_wait != 0:
            actions.add_wait(merged_opts.mouse_button_down_wait)
        actions.add_button_up(button)
        if merged_opts.mouse_button_up_wait != 0:
            actions.add_wait(merged_opts.mouse_button_up_wait)

    def _incremental_move(
        self,
        actions,
        from_point,
        to_point,
        merged_opts,
        start_increment=0
    ):
        if to_point == from_point:
            return
        (from_x, from_y), (to_x, to_y) = from_point, to_point
        x_distance = to_x - from_x
        y_distance = to_y - from_y
        distance_to_move = (x_distance ** 2 + y_distance ** 2) ** 0.5
        num_increments = int(distance_to_move //
                             merged_opts.mouse_move_increment)
        if num_increments > 0:
            inc_x = x_distance / num_increments
            inc_y = y_distance / num_increments
            for i in range(start_increment, num_increments):
                actions.add_move((int(from_x + (inc_x*i)), int(from_y + (inc_y*i))))
                if merged_opts.mouse_move_wait != 0:
                    actions.add_wait(merged_opts.mouse_move_wait)
        actions.add_move(to_point)
        if merged_opts.mouse_move_wait != 0:
            actions.add_wait(merged_opts.mouse_move_wait)

    def capture_locations(self):
        return LocationList(self._backend.capture_locations())

    def cursor_location(self):
        x, y = self._backend.cursor_position()
        return Location(x, y)

    def find_all(self, finder):
        return LocationList(self._find_all_gen(finder))

    def wait_find_with_result_matcher(self, finder, matcher, **options):
        start_time = time.time()
        while True:
            results = self.find_all(finder)
            if matcher.matches(results):
                return results
            if time.time() - start_time > self._opts.merge(options).timeout:
                raise NotFoundError("Waited for results matching %s from %s."
                                    "Last result %r" % (
                                        describe_to_string(matcher),
                                        finder,
                                        results))

    def wait_find_n(self, n, finder, **options):
        return self.wait_find_with_result_matcher(
            finder,
            has_length(n),
            **options
        )

    def wait_find_one(self, finder, **options):
        return self.wait_find_n(1, finder, **options)[0]

    def drag(self, from_finder, to_finder, **options):
        merged_opts = self._opts.merge(options)
        from_location = self.wait_find_one(from_finder, **options)
        to_location = self.wait_find_one(to_finder, **options)
        from_point = from_location.main_point
        to_point = to_location.main_point
        with self._backend.actions_transaction() as actions:
            self._move(actions, from_point, merged_opts)
            actions.add_button_down(1)
            if merged_opts.mouse_button_down_wait != 0:
                actions.add_wait(merged_opts.mouse_button_down_wait)
            if not merged_opts.mouse_warp_dragging:
                self._incremental_move(
                    actions,
                    from_point,
                    to_point,
                    merged_opts,
                    start_increment=1
                )
            actions.add_move(to_point)
            if merged_opts.mouse_move_wait != 0:
                actions.add_wait(merged_opts.mouse_move_wait)
            actions.add_button_up(1)
            if merged_opts.mouse_button_up_wait != 0:
                actions.add_wait(merged_opts.mouse_button_up_wait)
        return from_location, to_location

    def drag_relative(self, from_finder, offset, **options):
        from_location = self.wait_find_one(from_finder, **options)
        from_x, from_y = from_location.main_point
        to_x, to_y = (from_x + offset[0], from_y + offset[1])
        return self.drag(
            from_location,
            Location(to_x, to_y),
            **options
        )
        from_location

    def move(self, finder, **options):
        merged_opts = self._opts.merge(options)
        location = self.wait_find_one(finder, **options)
        with self._backend.actions_transaction() as actions:
            self._move(actions, location.main_point, merged_opts)
        if merged_opts.wait_for_image_change_post_action:
            self._wait_for_image_change(location, merged_opts)
        return location

    def _click(self, finder, button, times, options):
        merged_opts = self._opts.merge(options)
        location = self.wait_find_one(finder, **options)
        with self._backend.actions_transaction() as actions:
            self._move(actions, location.main_point, merged_opts)
        if merged_opts.wait_for_image_change_pre_action:
            self._wait_for_image_change(location, merged_opts)
        with self._backend.actions_transaction() as actions:
            for i in range(times):
                self._button_click(actions, button, merged_opts)
        if merged_opts.wait_for_image_change_post_action:
            self._wait_for_image_change(location, merged_opts)
        return location

    def click(self, finder, **options):
        self._click(finder, 1, 1, options)

    def double_click(self, finder, **options):
        self._click(finder, 1, 2, options)

    def context_click(self, finder, **options):
        self._click(finder, 3, 1, options)

    def key_presses(self, *text_or_keys, **options):
        merged_opts = self._opts.merge(options)
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
                    if merged_opts.key_down_wait != 0:
                        actions.add_wait(merged_opts.key_down_wait)
                elif isinstance(key_action, KeyUp):
                    actions.add_key_up(str(key_action))
                    if merged_opts.key_up_wait != 0:
                        actions.add_wait(merged_opts.key_up_wait)
                else:
                    raise ValueError('Key action must be a KeyUp or KeyDown')

    def exists(self, finder):
        return True if self.find_all(finder) else False

    def exists_within_timeout(self, finder, **options):
        try:
            self.wait_find_with_result_matcher(
                finder,
                has_length(greater_than_or_equal_to(1)),
                **options
            )
            return True
        except NotFoundError:
            return False

    def does_not_exist_within_timeout(self, finder, **options):
        try:
            self.wait_find_with_result_matcher(
                finder,
                has_length(less_than_or_equal_to(0)),
                **options
            )
            return True
        except NotFoundError:
            return False

