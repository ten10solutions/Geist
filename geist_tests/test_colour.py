import unittest
import numpy as np
from numpy.testing import assert_array_equal
from geist.colour import rgb_to_hsv
from ._common import logger as base_logger

logger = base_logger.getChild('colour')


class TestColorSpaceMaps(unittest.TestCase):
    def test_rgb_to_hsv(self):
        image = np.array(
            [[[1, 2, 3], [0, 0, 0]],
             [[0, 0, 0], [1, 1, 1]]])
        expected = np.array(
            [[[149, 0], [0, 0]],
             [[170, 0], [0, 0]],
             [[3, 0], [0, 1]]])
        actual = rgb_to_hsv(image)
        assert_array_equal(actual, expected)


colour_space_suite = unittest.TestLoader().loadTestsFromTestCase(
    TestColorSpaceMaps)
all_tests = unittest.TestSuite([colour_space_suite])
if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(all_tests)
