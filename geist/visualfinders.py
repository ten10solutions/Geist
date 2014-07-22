from __future__ import division, absolute_import, print_function

from .finders import Location
from .vision import best_convolution, grey_scale, find_edges
from .colour import rgb_to_hsv
from .ocr import Classifier
import numpy
from scipy.ndimage.measurements import (
    label,
    find_objects,
)
from scipy.ndimage.morphology import binary_propagation, binary_erosion
import logging
from .finders import BaseFinder

logger = logging.getLogger(__name__)


class TextFinderFilter(BaseFinder):
    def __init__(self, classifier, finder, text):
        self.classifier = classifier
        self.text = text
        self.finder = finder

    def find(self, in_location):
        image = in_location.image
        for loc in self.finder.find(in_location):
            sub_image = image[loc.y:loc.y + loc.h, loc.x:loc.x + loc.w]
            text = self.classifier.classify(sub_image)
            if text.replace('?', '') == self.text:
                yield loc


def text_finder_filter_from_path(path):
    classifier = Classifier()
    with open(path) as f:
        classifier.from_json(f.read())
    return lambda finder, text: TextFinderFilter(classifier, finder, text)


class ThresholdTemplateFinder(BaseFinder):
    def __init__(self, template, threshold=10):
        self.template = template
        self.threshold = threshold

    def find(self, in_location):
        h, w = self.template.image.shape[:2]
        image = in_location.image
        gimage = grey_scale(image)
        gtemplate = grey_scale(self.template.image)
        threshold_image = gimage > self.threshold
        threshold_template = gtemplate > self.threshold
        edge_image = find_edges(threshold_image)
        edge_template = find_edges(threshold_template)
        bin_image = edge_image > 0
        bin_template = edge_template > 0
        for x, y in best_convolution(bin_template, bin_image):
            yield Location(x, y, w, h, parent=in_location)

    def __repr__(self):
        return "match %r using threshold %r" % (self.template, self.threshold)


class ApproxTemplateFinder(BaseFinder):
    def __init__(self, template):
        self.template = template

    def find(self, in_location):
        h, w = self.template.image.shape[:2]
        image = in_location.image
        gimage = grey_scale(image)
        gtemplate = grey_scale(self.template.image)
        edge_image = find_edges(gimage)
        edge_template = find_edges(gtemplate)
        bin_image = edge_image > 10
        bin_template = edge_template > 10
        for x, y in best_convolution(bin_template, bin_image):
            yield Location(x, y, w, h, parent=in_location)

    def __repr__(self):
        return "match %r approximately" % (self.template, )


class ExactTemplateFinder(BaseFinder):
    def __init__(self, template):
        self.template = template
        self.approx_template_finder = ApproxTemplateFinder(self.template)

    def find(self, in_location):
        image = in_location.image
        ih, iw = image.shape[:2]
        th, tw = self.template.image.shape[:2]
        for location in self.approx_template_finder.find(in_location):
            x, y = location.rel_x, location.rel_y
            if (x >= 0 and y >= 0 and x + tw <= iw and y + th <= ih):
                if numpy.all(
                    numpy.equal(image[y:y + th, x:x + tw], self.template.image)
                ):
                    yield location

    def __repr__(self):
        return "match %r exactly" % (self.template, )


class MultipleFinderFinder(BaseFinder):
    def __init__(self, *finders):
        self.finders = finders

    def find(self, in_location):
        for finder in self.finders:
            for location in finder.find(in_location):
                yield location


class BinaryRegionFinder(BaseFinder):
    def __init__(self, binary_image_function):
        self.binary_image_function = binary_image_function

    def find(self, in_location):
        image = in_location.image
        bin_image = self.binary_image_function(image)
        for y_slice, x_slice in find_objects(*label(bin_image)):
            yield Location(
                x_slice.start,
                y_slice.start,
                x_slice.stop - x_slice.start,
                y_slice.stop - y_slice.start,
                parent=in_location
            )


class ColourRegionFinder(BaseFinder):
    def __init__(self, colour_filter):
        self.binary_finder = BinaryRegionFinder(
            lambda image: colour_filter(*rgb_to_hsv(image))
        )

    def find(self, in_location):
        return self.binary_finder.find(in_location)


class GreyscaleRegionFinder(BaseFinder):
    def __init__(self, grey_scale_filter):
        self.binary_finder = BinaryRegionFinder(
            lambda image: grey_scale_filter(grey_scale(image))
        )

    def find(self, in_location):
        return self.binary_finder.find(in_location)


class ContainerFinder(BaseFinder):
    def __init__(self, finder, binary_image_function):
        self._binary_image_function = binary_image_function
        self._finder = finder

    def find(self, in_location):
        image = in_location.image
        processed_image = self._binary_image_function(image)
        mask = processed_image == False
        propagation_input = numpy.zeros_like(processed_image)
        for loc in self._finder.find(in_location):
            propagation_input[loc.y:loc.y+loc.h, loc.x:loc.x+loc.w] = True
        propagation = binary_propagation(propagation_input, mask=mask)
        for y_slice, x_slice in find_objects(*label(propagation)):
            yield Location(
                x_slice.start,
                y_slice.start,
                x_slice.stop - x_slice.start,
                y_slice.stop - y_slice.start,
                parent=in_location
            )
