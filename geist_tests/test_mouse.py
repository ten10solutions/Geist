from __future__ import division, absolute_import, print_function
import os
import unittest
from geist import Location, GUI, LocationList
from geist.backends.windows import _Mouse, _ActionsTransaction
import concurrent.futures
import time
import numpy as np

from ctypes  import windll, pointer, c_long, c_ulong, Structure

        
        
class _point_t(Structure):
    _fields_ = [
                ('x',  c_long),
                ('y',  c_long),
               ]
  
def get_cursor_position():
    point = _point_t()
    result = windll.user32.GetCursorPos(pointer(point))
    if result:  return (point.x, point.y)
    else:       return None

        
def get_mouse_positions():
    start = time.time()
    positions = []
    while drag_mouse.result == None and time.time() < start + 10:
        positions.append(get_cursor_position())
        
       

class GeistMouseBackend(object):
    def __init__(self, **kwargs):
        self._mouse = _Mouse()
        self.list = []
        image = kwargs.get('image')
        w = kwargs.get('w', 1000)
        h = kwargs.get('h', 1000)
        
        if image is None:
            self.image = np.zeros((h, w, 3), dtype=np.ubyte)
            self.locations = LocationList(
                [Location(0, 0, w=w, h=h, image=self.image)]
            )
        else:
            if isinstance(image, basestring):
                image = np.load(image)
            self.image = image
            h, w, _ = image.shape
            self.locations = LocationList(
                [Location(0, 0, w=w, h=h, image=self.image)]
            )
            
            
    def move(self, point):
        self._mouse.move(point)
        self.list.append(get_cursor_position())
        
    def create_process(self, command):
        raise AssertionError

    def actions_transaction(self):
        return _ActionsTransaction(self)

    def capture_locations(self):
        for loc in self.locations:
            yield loc

    def key_down(self, name):
        raise AssertionError

    def key_up(self, name):
        raise AssertionError

    def button_down(self, button_num):
        self._mouse.button_down(button_num)

    def button_up(self, button_num):
        self._mouse.button_up(button_num)
    def close(self):
        raise AssertionError

    
class TestMouseDrag(unittest.TestCase):
    # need ot be getting cursor position while the drag operation is happening
    # need to define functions to run concurrently
    def test_mouse_drag_y_dir(self):
        backend = GeistMouseBackend()
        #print(type(backend))
        gui = GUI(backend)
        #print(type(gui))
        gui.drag_incremental(Location(200,200), Location(201,900))
        # this overshoots on y then goes back, not ideal!!
        positions = [(200,200), (200, 270), (200, 340),(200, 410),(200, 480),
                            (200, 550),(200, 620),(200, 690),(200, 760),(200, 830), (201,900)]
        print(backend.list)                    
        self.assertEquals(sorted(positions), sorted(backend.list))
        
    def test_mouse_drag_equal_dirs(self):
        backend = GeistMouseBackend()
        #print(type(backend))
        gui = GUI(backend)
        #print(type(gui))
        gui.drag_incremental(Location(200,200), Location(400, 400))
        positions = [(200,200),(235, 235), (270, 270), (305, 305), (340, 340), (400,400)]
        print(backend.list)         
        self.assertEquals(sorted(positions), sorted(backend.list))
        
        
replay_suite = unittest.TestLoader().loadTestsFromTestCase(TestMouseDrag)
all_tests = unittest.TestSuite([replay_suite])

if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(all_tests)
