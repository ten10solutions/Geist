from __future__ import division, absolute_import, print_function

import time
import logging
from hamcrest import (
    has_length, greater_than_or_equal_to, less_than_or_equal_to)
from hamcrest.core.string_description import tostring as describe_to_string
import math
from .keyboard import KeyDown, KeyUp, KeyDownUp, keyboard_layout_factory
from .finders import LocationList


logger = logging.getLogger(__name__)


class NotFoundError(LookupError):
    """Raised when something couldn't be found
    """
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
        _from = (int(_from[0]), int(_from[1]))
        to = (int(to[0]), int(to[1]))
        with self._backend.actions_transaction() as actions:
            actions.add_move(_from)
            actions.add_wait(self.config_mouse_move_wait)
            actions.add_button_down(1)
            actions.add_wait(self.config_mouse_button_wait)
            actions.add_move(to)
            actions.add_wait(self.config_mouse_move_wait)
            actions.add_button_up(1)
            actions.add_wait(self.config_mouse_button_wait)
            
            
    def drag_incremental(self, from_finder, to_finder, increment=50):
        _from = self.wait_find_one(from_finder).main_point
        to = self.wait_find_one(to_finder).main_point
        _from = (int(_from[0]), int(_from[1]))
        to = (int(to[0]), int(to[1]))
        x_distance = to[0] - _from[0] 
        y_distance = to[1] - _from[1] 
        distance = math.sqrt(x_distance**2+y_distance**2)
        #print x_distance, y_distance
        if x_distance >= 0:
              x_mult = 1
        else:
              x_mult  = -1
        if y_distance >= 0:
              y_mult = 1
        else:
              y_mult = -1
        # use exponents so one sum can do all 4 cases
        total_distance_per_move = math.sqrt(2*increment**2)
        number_moves = int(distance/total_distance_per_move)
        if x_distance != 0 and y_distance !=0:
            # if x_dist = y_dist, get 1- should be 0.5- just multiply?
            x_y_ratio = 0.5*(x_distance/y_distance)
        elif x_distance == 0:
            x_y_ratio = 0
        elif y_distance == 0:
            x_y_ratio = 1
        x_step = int(x_y_ratio*total_distance_per_move)
        y_step = int((1-x_y_ratio)*total_distance_per_move)
        #print x_y_ratio, x_step, y_step, number_moves
        with self._backend.actions_transaction() as actions:
                actions.add_move(_from)
                actions.add_wait(self.config_mouse_move_wait)
                actions.add_button_down(1)
                for i in range(1, int(number_moves+1)):
                    next_point = (_from[0] + ((i*x_step)*x_mult), _from[1] + ((i*y_step)*y_mult))
                    if next_point[0] < 0 or next_point[1] < 0:
                        raise ValueError('Tried to move to point (%d, %d)' % point)
                    actions.add_move(next_point)
                    actions.add_wait(self.config_mouse_button_wait)
                    #print next_point, ((i*x_step)*x_mult), ((i*y_step)*y_mult), x_step, i*x_step
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
