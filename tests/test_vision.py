import numpy as np
import unittest
from geist.vision import convolution, overlapped_convolution

from tests import logger as base_logger

logger = base_logger.getChild('vision')


class TestOverlappedConvolution(unittest.TestCase):
    def test_no_match(self):
        blank = np.zeros((100, 100))
        template = np.array([[0, 1], [1, 0]])

        expected = []
        actual = overlapped_convolution(template, blank)
        self.assertEquals(expected, actual)

    @unittest.skip('wip')
    def test_match(self):
        image = np.array([[0, 0, 0, 0],
                          [0, 1, 0, 0],
                          [1, 0, 0, 0],
                          [0, 0, 0, 0]])
        template = np.array([[0, 1], [1, 0]])

        expected = []
        actual = overlapped_convolution(template, image)
        self.assertEquals(expected, actual)


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


convolution_suite = unittest.TestLoader().loadTestsFromTestCase(
    TestConvolution)
overlapped_convolution_suite = unittest.TestLoader().loadTestsFromTestCase(
    TestOverlappedConvolution)
all_tests = unittest.TestSuite([convolution_suite,
                                overlapped_convolution_suite])
if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(all_tests)
