from itertools import cycle
from matplotlib.pyplot import cm, figure, gcf, imshow
from geist.colour import rgb_to_hsv, hsv
import numpy


class Viewer(object):
    def __init__(self, gui, repo):
        self._gui = gui
        self._repo = repo

    def save(self, name):
        self._repo[name] = self.visible()

    def visible(self):
        a = gcf().get_axes()[0]
        x1, x2 = a.get_xbound()
        y1, y2 = a.get_ybound()
        x1 = int(x1 + 0.5)
        x2 = int(numpy.ceil(x2 + 0.5))
        y1 = int(y1 + 0.5)
        y2 = int(numpy.ceil(y2 + 0.5))
        return numpy.array(a.get_images()[-1].get_array()[y1:y2, x1:x2])

    def show_capture(self):
        for location in self._gui.capture_locations():
            figure()
            imshow(location.image, interpolation='none')

    def show_repo(self, name, newfig=False):
        if newfig:
            figure()
        imshow(self._repo[name].image, cm.Greys_r, interpolation='none')

    def show_image(self, image):
        imshow(image, interpolation='none')

    def show_found(self, finder):
        for location in self._gui.capture_locations():
            figure()
            image = numpy.copy(location.image)
            channel = cycle([0, 1, 2])
            for l, c in zip(finder.find(location), channel):
                image[l.y:l.y + l.h, l.x:l.x + l.w, :] *= 0.75
                image[l.y:l.y + l.h, l.x:l.x + l.w, c] = 255
            imshow(image, interpolation='none')
    
    def _get_colour(self, numpy_array):
        hue, sat, val = rgb_to_hsv(numpy_array)
        hmin = hue.min()
        hmax = hue.max()
        smin = sat.min()
        smax = sat.max()
        vmin = val.min()
        vmax = val.max()
        return hsv(lambda h, s, v: (
            (h >= hmin) & (h <= hmax)) &
            ((s >= smin) & (s <= smax)) &
            ((v >= vmin) & (v <= vmax)))
 

    def get_colour(self):
        return self._get_colour(self.visible())
