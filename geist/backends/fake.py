import numpy as np
from ..core import Location


class GeistFakeBackend(object):
    def __init__(self, w=800, h=600):
        self.image = np.zeros((h, w, 3))
        self.locations = [Location(0, 0, w=w, h=h, image=self.image)]

    def create_process(self, command):
        pass

    def actions_transaction(self):
        pass

    def capture_locations(self):
        for loc in self.locations:
            yield loc

    def key_down(self, name):
        pass

    def key_up(self, name):
        pass

    def button_down(self, button_num):
        pass

    def button_up(self, button_num):
        pass

    def move(self, point):
        pass

    def close(self):
        pass
