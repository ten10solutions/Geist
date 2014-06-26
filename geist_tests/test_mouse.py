from __future__ import division, absolute_import, print_function
import os
import unittest
from geist import Location, GUI, LocationList
import time
import numpy as np
from geist.backends.fake import GeistFakeBackend

class FakeBackendActionBuilder(object):
    def __init__(self, backend):
        self._backend = backend
        self._actions = []

    def add_move(self, point):
        self._actions.append(lambda: self._backend.move(point))

    def add_wait(self, seconds):
        self._actions.append(lambda: time.sleep(seconds))

    def add_button_down(self, *args):
        self._actions.append(lambda: self._backend.button_down())

    def add_button_up(self, *args):
        self._actions.append(lambda: self._backend.button_up())

    def execute(self):
        for action in self._actions:
           action()


class FakeActionsTransaction(object):
    def __init__(self, backend):
        self._actions_builder = FakeBackendActionBuilder(backend)

    def __enter__(self):
        return self._actions_builder

    def __exit__(self, *args):
        self._actions_builder.execute()
        return False


class GeistMouseBackend(GeistFakeBackend):
    def __init__(self):
        super(GeistMouseBackend, self).__init__(h=1000, w=1000)
        self.list_of_points = []
        self.button_down_pressed = False
        self.button_up_pressed = False

    def move(self, point):
        print(point)
        self.list_of_points.append(point)
        print(self.list_of_points)

    def actions_transaction(self):
        return FakeActionsTransaction(self)

    def button_down(self):
        self.button_down_pressed = True

    def button_up(self):
        if self.button_down_pressed == False:
            # can't imagine why we'd ever want to have the button come up before its gone down
            raise AssertionError
        else:
            self.button_up_pressed = True



class TestMouseDrag(unittest.TestCase):
    # need ot be getting cursor position while the drag operation is happening
    # need to define functions to run concurrently
    def test_mouse_drag_y_dir(self):
        backend = GeistMouseBackend()
        gui = GUI(backend)
        gui.drag(Location(200,200), Location(201,900))
        # this overshoots on y then goes back, not ideal!!
        positions = [(200,200), (200, 270), (200, 340),(200, 410),(200, 480),
                            (200, 550),(200, 620),(200, 690),(200, 760),(200, 830), (201,900)]
        self.assertEquals(sorted(positions), sorted(backend.list_of_points))
        self.assertTrue(backend.button_down_pressed)
        self.assertTrue(backend.button_up_pressed)

    def test_mouse_drag_equal_dirs(self):
        backend = GeistMouseBackend()
        gui = GUI(backend)
        gui.drag(Location(200,200), Location(400, 400))
        positions = [(200,200),(235, 235), (270, 270), (305, 305), (340, 340), (400,400)]
        self.assertEquals(sorted(positions), sorted(backend.list_of_points))
        self.assertTrue(backend.button_down_pressed)
        self.assertTrue(backend.button_up_pressed)

    def test_mouse_drag_x_dir(self):
        backend = GeistMouseBackend()
        gui = GUI(backend)
        gui.drag(Location(200,200), Location(0, 200))
        positions = [(200,200),(130, 200), (60, 200), (0, 200)]
        self.assertEquals(sorted(positions), sorted(backend.list_of_points))
        self.assertTrue(backend.button_down_pressed)
        self.assertTrue(backend.button_up_pressed)


replay_suite = unittest.TestLoader().loadTestsFromTestCase(TestMouseDrag)
all_tests = unittest.TestSuite([replay_suite])

if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(all_tests)
