from __future__ import division, absolute_import, print_function

from .core import Location
from .vision import best_convolution, grey_scale, edge_enhance
from .colour import rgb_to_hsv
import numpy
from itertools import chain
from scipy.ndimage.measurements import (
    label,
    find_objects,
)

class ApproxTemplateFinder(object):
    def __init__(self, template):
        self.template = template

    def find(self, gui):
        h, w = self.template.shape[:2]
        image = gui.capture()
        gimage = grey_scale(image)
        gtemplate = grey_scale(self.template)
        edge_image = edge_enhance(gimage)
        edge_template = edge_enhance(gtemplate)
        bin_image = edge_image > 10
        bin_template = edge_template > 10
        for x, y in best_convolution(bin_template, bin_image):
            yield Location(x+1, y+1, w, h, image=image)


class ExactTemplateFinder(object):
    def __init__(self, template):
        self.template = template
        self.approx_template_finder = ApproxTemplateFinder(self.template)

    def find(self, gui):
        image = gui.capture()
        ih, iw = image.shape[:2]
        th, tw = self.template.shape[:2]
        for location in self.approx_template_finder.find(gui):
            x, y = location.x, location.y
            if (x >= 0 and y >= 0 and x + tw <= iw and y + th <= ih):
                if numpy.all(
                    numpy.equal(image[y:y+th, x:x+tw], self.template)
                ):
                    yield location


class ThresholdTemplateFinder(object):
    def __init__(self, template, threshold):
        self.template = template
        self.threshold = threshold

    def find(self, gui):
        h, w = self.template.shape[:2]
        image = gui.capture()
        gimage = grey_scale(image)
        gtemplate = grey_scale(self.template)
        threshold_image = gimage > self.threshold
        threshold_template = gtemplate > self.threshold
        edge_image = edge_enhance(threshold_image)
        edge_template = edge_enhance(threshold_template)
        bin_image = edge_image > 0
        bin_template = edge_template > 0
        for x, y in best_convolution(bin_template, bin_image):
            yield Location(x+1, y+1, w, h, image=image)


class MultipleFinderFinder(object):
    def __init__(self, *finders):
        self.finders = finders

    def find(self, gui):
        return chain(finder.find(gui) for finder in self.finders)


class BinaryRegionFinder(object):
    def __init__(self, binary_image_function):
        self.binary_image_function = binary_image_function

    def find(self, gui):
        image = gui.capture()
        bin_image = self.binary_image_function(image)
        for y_slice, x_slice in find_objects(*label(bin_image)):
            yield Location(
                x_slice.start,
                y_slice.start,
                x_slice.stop - x_slice.start,
                y_slice.stop - y_slice.start,
                image=image
            )


class ColourRegionFinder(object):
    def __init__(self, colour_filter):
        self.binary_finder = BinaryRegionFinder(
            lambda image: colour_filter(*rgb_to_hsv(image))
        )

    def find(self, gui):
        return self.binary_finder.find(gui)


class GreyscaleRegionFinder(object):
    def __init__(self, grey_scale_filter):
        self.binary_finder = BinaryRegionFinder(
            lambda image: grey_scale_filter(grey_scale(image))
        )

    def find(self, gui):
        return self.binary_finder.find(gui)
