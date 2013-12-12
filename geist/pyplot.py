from matplotlib.pyplot import *
import numpy
from itertools import cycle

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
        x1 = int(x1+0.5)
        x2 = int(numpy.ceil(x2+0.5))
        y1 = int(y1+0.5)
        y2 = int(numpy.ceil(y2+0.5))
        return numpy.array(a.get_images()[-1].get_array()[y1:y2,x1:x2])

    def show_capture(self, newfig=False):
        if newfig:
            figure()
        imshow(self._gui.capture(), interpolation='none')

    def show_repo(self, name, newfig=False):
        if newfig:
            figure()
        imshow(self._repo[name].image, cm.Greys_r, interpolation='none')

    def show_image(self, image):
        imshow(image, interpolation='none')

    def show_found(self, finder):
        image = self._gui.capture()
        channel = cycle([0,1,2])
        for l, c in zip(self._gui.find_all(finder), channel):
            image[l.y:l.y+l.h, l.x:l.x+l.w,:] *= 0.75
            image[l.y:l.y+l.h, l.x:l.x+l.w, c] = 255

        imshow(image, interpolation='none')
