import numpy as np
from ..core import Location, LocationList


class GeistFakeBackend(object):
    def __init__(self, **kwargs):
        image = kwargs.get('image')
        w = kwargs.get('w', 800)
        h = kwargs.get('h', 600)

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
