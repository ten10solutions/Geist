from matplotlib.pyplot import *
import numpy

class Viewer(object):
    def __init__(self, **kwargs):
        self.__C = dict(kwargs)

    def save(self, name):
        self.__C['repo'][name] = self.visible()

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
        imshow(self.__C['capture'](), interpolation='none')

    def show_repo(self, name, newfig=False):
        if newfig:
            figure()
        imshow(self.__C['repo'][name], cm.Greys_r, interpolation='none')

    def show_image(self, image):
        imshow(image, interpolation='none')

