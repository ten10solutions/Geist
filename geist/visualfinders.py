from __future__ import division, absolute_import, print_function

from .core import Location
from .vision import best_convolution, grey_scale, find_edges
from .colour import rgb_to_hsv
from .ocr import Classifier
import numpy
from scipy.ndimage.measurements import (
    label,
    find_objects,
)
import logging

logger = logging.getLogger(__name__)


class TextFinderFilter(object):
    def __init__(self, classifier, finder, text):
        self.classifier = classifier
        self.text = text
        self.finder = finder

    def find(self, gui):
        image = gui.capture()
        for loc in self.finder.find(gui):
            sub_image = image[loc.y:loc.y + loc.h, loc.x:loc.x + loc.w]
            text = self.classifier.classify(sub_image)
            if text.replace('?','') == self.text:
                yield loc


def text_finder_filter_from_path(path):
    classifier = Classifier()
    with open(path) as f:
        classifier.from_json(f.read())
    return lambda finder, text: TextFinderFilter(classifier, finder, text)


class ApproxTemplateFinder(object):
    def __init__(self, template):
        self.template = template

    def find(self, gui):
        h, w = self.template.image.shape[:2]
        image = gui.capture()
        gimage = grey_scale(image)
        gtemplate = grey_scale(self.template.image)
        edge_image = find_edges(gimage)
        edge_template = find_edges(gtemplate)
        bin_image = edge_image > 10
        bin_template = edge_template > 10
        for x, y in best_convolution(bin_template, bin_image):
            yield Location(x+1, y+1, w, h, image=image)

    def __repr__(self):
        return "match %r approximately" % (self.template, )


class ExactTemplateFinder(object):
    def __init__(self, template):
        self.template = template
        self.approx_template_finder = ApproxTemplateFinder(self.template)

    def find(self, gui):
        image = gui.capture()
        ih, iw = image.shape[:2]
        th, tw = self.template.image.shape[:2]
        for location in self.approx_template_finder.find(gui):
            x, y = location.x, location.y
            if (x >= 0 and y >= 0 and x + tw <= iw and y + th <= ih):
                if numpy.all(
                    numpy.equal(image[y:y+th, x:x+tw], self.template)
                ):
                    yield location

    def __repr__(self):
        return "match %r exactly" % (self.template, )


class ThresholdTemplateFinder(object):
    def __init__(self, template, threshold):
        self.template = template
        self.threshold = threshold

    def find(self, gui):
        h, w = self.template.image.shape[:2]
        image = gui.capture()
        gimage = grey_scale(image)
        gtemplate = grey_scale(self.template.image)
        threshold_image = gimage > self.threshold
        threshold_template = gtemplate > self.threshold
        edge_image = find_edges(threshold_image)
        edge_template = find_edges(threshold_template)
        bin_image = edge_image > 0
        bin_template = edge_template > 0
        for x, y in best_convolution(bin_template, bin_image):
            yield Location(x+1, y+1, w, h, image=image)

    def __repr__(self):
        return "match %r using threshold %r" % (self.template, self.threshold)


class MultipleFinderFinder(object):
    def __init__(self, *finders):
        self.finders = finders

    def find(self, gui):
        for finder in self.finders:
            for location in finder.find(gui):
                yield location


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
