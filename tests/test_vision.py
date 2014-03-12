import numpy as np
from numpy.testing import assert_array_equal
import unittest
from geist.vision import (best_convolution,
                          convolution, overlapped_convolution,
                          pad_bin_image_to_shape)

from tests import logger as base_logger

logger = base_logger.getChild('vision')


class TestOverlappedConvolution(unittest.TestCase):
    def test_no_match(self):
        blank = np.zeros((100, 100))
        template = np.array([[0, 1], [1, 0]])

        expected = []
        actual = overlapped_convolution(template, blank)
        self.assertEquals(expected, actual)

    def test_match(self):
        image = np.array([[0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 1, 0],
                          [0, 0, 0, 0, 0, 1, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 1, 0, 0, 0, 0, 0],
                          [0, 1, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0]])
        template = np.array([[0, 1], [1, 0]])

        expected = [(1, 5), (5, 2)]
        actual = overlapped_convolution(template, image)
        self.assertEquals(sorted(expected), sorted(actual))

    def test_edge_overlap(self):
        """
        When an image is split and reconstructed such that image parts combine
        to appear like the template, we can get false positives in strange
        places.
        """
        image = np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                          [1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
                          [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                          [1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])
        template = np.array([[1, 1, 1],
                             [0, 1, 0],
                             [1, 1, 1]])

        expected = []
        actual = overlapped_convolution(template, image)
        self.assertEquals(sorted(expected), sorted(actual))


class TestConvolution(unittest.TestCase):
    def test_no_match(self):
        blank = np.zeros((4, 4))
        template = np.array([[0, 1], [1, 0]])

        expected = []
        actual = convolution(template, blank)
        self.assertEquals(expected, actual)

    def test_match(self):
        image = np.array([[0, 0, 0, 0],
                          [0, 1, 0, 0],
                          [1, 0, 0, 0],
                          [0, 0, 0, 0]])
        template = np.array([[0, 1], [1, 0]])

        expected = [(0, 1)]
        actual = convolution(template, image)
        self.assertEquals(expected, actual)


class TestBestConvolution(unittest.TestCase):
    def test_no_match(self):
        blank = np.zeros((100, 100))
        template = np.array([[0, 1], [1, 0]])

        expected = []
        actual = best_convolution(template, blank)
        self.assertEquals(expected, actual)

    def test_match(self):
        image = np.array([[0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 1, 0],
                          [0, 0, 0, 0, 0, 1, 0, 0],
                          [0, 0, 0, 1, 0, 0, 0, 0],
                          [0, 0, 1, 0, 0, 0, 0, 0],
                          [0, 1, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0]])
        template = np.array([[0, 1], [1, 0]])

        expected = [(1, 5), (5, 2), (2, 4)]
        actual = best_convolution(template, image)
        self.assertEquals(sorted(expected), sorted(actual))

    def test_template_too_big(self):
        template = np.array([[0, 0, 0, 0, 0, 0, 0, 0],
                             [0, 0, 0, 0, 0, 0, 0, 0],
                             [0, 0, 0, 0, 0, 0, 1, 0],
                             [0, 0, 0, 0, 0, 1, 0, 0],
                             [0, 0, 0, 0, 0, 0, 0, 0],
                             [0, 0, 1, 0, 0, 0, 0, 0],
                             [0, 1, 0, 0, 0, 0, 0, 0],
                             [0, 0, 0, 0, 0, 0, 0, 0]])
        image = np.array([[0, 1], [1, 0]])

        expected = []
        actual = best_convolution(template, image)
        self.assertEquals(sorted(expected), sorted(actual))


class TestPadBinImageToShape(unittest.TestCase):
    def test_same_size(self):
        image = np.array([[0, 0, 0, 0, 0],
                          [0, 0, 0, 1, 0],
                          [0, 0, 1, 0, 0],
                          [0, 1, 0, 0, 0],
                          [0, 0, 0, 0, 0]])
        expected = image
        actual = pad_bin_image_to_shape(image, image.shape)
        assert_array_equal(expected, actual)

    def test_padding(self):
        image = np.array([[0, 0, 0, 0, 0],
                          [0, 0, 0, 1, 0],
                          [0, 0, 1, 0, 0],
                          [0, 1, 0, 0, 0],
                          [0, 0, 0, 0, 0]])
        expected = np.array([[0, 0, 0, 0, 0, 0, 0, 0],
                             [0, 0, 0, 1, 0, 0, 0, 0],
                             [0, 0, 1, 0, 0, 0, 0, 0],
                             [0, 1, 0, 0, 0, 0, 0, 0],
                             [0, 0, 0, 0, 0, 0, 0, 0],
                             [0, 0, 0, 0, 0, 0, 0, 0]])
        actual = pad_bin_image_to_shape(image, (6, 8))
        assert_array_equal(expected, actual)


best_convolution_suite = unittest.TestLoader().loadTestsFromTestCase(
    TestBestConvolution)
convolution_suite = unittest.TestLoader().loadTestsFromTestCase(
    TestConvolution)
overlapped_convolution_suite = unittest.TestLoader().loadTestsFromTestCase(
    TestOverlappedConvolution)
pad_bin_image_to_shape_suite = unittest.TestLoader().loadTestsFromTestCase(
    TestPadBinImageToShape)
all_tests = unittest.TestSuite([best_convolution_suite,
                                convolution_suite,
                                overlapped_convolution_suite,
                                pad_bin_image_to_shape_suite,
                                ])
if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(all_tests)
