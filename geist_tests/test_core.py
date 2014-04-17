import unittest
import numpy as np
from numpy.testing import assert_array_equal

from geist.core import Location
from geist_tests import logger as base_logger

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
        assert_array_equal(loc.image, image)

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

    def test_parent_x(self):
        image = np.array([[0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 1, 0],
                          [0, 0, 0, 0, 0, 1, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 1, 0, 0, 0, 0, 0],
                          [0, 1, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0]])
        parent = Location(0, 0, w=8, h=8, image=image)
        loc = Location(2, 2, parent=parent)
        self.assertEquals(loc.x, 2)

    def test_parent_y(self):
        image = np.array([[0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 1, 0],
                          [0, 0, 0, 0, 0, 1, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 1, 0, 0, 0, 0, 0],
                          [0, 1, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0]])
        parent = Location(0, 0, w=8, h=8, image=image)
        loc = Location(2, 2, parent=parent)
        self.assertEquals(loc.y, 2)

    def test_copy(self):
        image = np.array([[0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 1, 0],
                          [0, 0, 0, 0, 0, 1, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 1, 0, 0, 0, 0, 0],
                          [0, 1, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0]])
        loc = Location(0, 0, w=8, h=8, image=image)
        copy = loc.copy(rel_x=7)
        self.assertEquals(copy.x, 7)

    def test_area(self):
        image = np.array([[0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 1, 0],
                          [0, 0, 0, 0, 0, 1, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 1, 0, 0, 0, 0, 0],
                          [0, 1, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0]])
        loc = Location(0, 0, w=8, h=8, image=image)
        self.assertEqual(loc.area, 64)

location_suite = unittest.TestLoader().loadTestsFromTestCase(TestLocation)
all_tests = unittest.TestSuite([location_suite])
if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(all_tests)
