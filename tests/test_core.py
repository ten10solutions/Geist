import unittest
import numpy as np

from geist.core import Location
from tests import logger as base_logger

logger = base_logger.getChild('filters')


class TestLocation(unittest.TestCase):
    def test_init(self):
        loc = Location(0, 0)
        self.assertTrue(loc)

    def test_negative_x(self):
        with self.assertRaises(ValueError):
            Location(-1, 0)

    def test_negative_y(self):
        with self.assertRaises(ValueError):
            Location(0, -1)

    def test_image(self):
        image = np.array([[0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 1, 0],
                          [0, 0, 0, 0, 0, 1, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 1, 0, 0, 0, 0, 0],
                          [0, 1, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0]])
        loc = Location(0, 0, w=8, h=8, image=image)
        self.assertEquals(loc)

    def test_image_no_dims(self):
        image = np.array([[0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 1, 0],
                          [0, 0, 0, 0, 0, 1, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 1, 0, 0, 0, 0, 0],
                          [0, 1, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0]])
        with self.assertRaises(AssertionError):
            Location(0, 0, image=image)

    def test_parent(self):
        parent = Location(0, 0)
        loc = Location(0, 0, parent=parent)
        self.assertEquals(loc.parent, parent)


location_suite = unittest.TestLoader().loadTestsFromTestCase(TestLocation)
all_tests = unittest.TestSuite([location_suite])
if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(all_tests)
