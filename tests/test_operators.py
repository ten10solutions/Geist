import unittest
from geist import Location, LocationList, GUI, LocationOperatorFinder
from geist.backends.fake import GeistFakeBackend
from geist.layoutfinders import below, left_of
from tests import logger as base_logger

logger = base_logger.getChild('operators')


class TestOperators(unittest.TestCase):
    def setUp(self):
        self.gui = GUI(GeistFakeBackend())
        self.screen = self.gui.capture_locations()[0]
        self.locs_a = LocationList([Location(10, 13, w=5, h=5, parent=self.screen)])
        self.locs_b = LocationList([Location(0, 2, w=5, h=5, parent=self.screen),
                                    Location(0, 24, w=5, h=5, parent=self.screen),
                                    Location(22, 2, w=5, h=5, parent=self.screen),
                                    Location(22, 24, w=5, h=5, parent=self.screen)])

    def test_and(self):
        below_and_left = below & left_of
        expected = [Location(0, 24, w=5, h=5, parent=self.screen)]
        finder = LocationOperatorFinder(self.locs_b, below_and_left,
                                        self.locs_a)
        actual = self.gui.find_all(finder)
        self.assertListEqual(actual, expected)

    def test_invert(self):
        not_below = ~below
        expected = [Location(0, 2, w=5, h=5, parent=self.screen),
                    Location(22, 2, w=5, h=5, parent=self.screen)]
        finder = LocationOperatorFinder(self.locs_b, not_below, self.locs_a)
        actual = self.gui.find_all(finder)
        self.assertListEqual(actual, expected)

    def test_or(self):
        below_or_left = below | left_of
        expected = [Location(0, 2, w=5, h=5, parent=self.screen),
                    Location(0, 24, w=5, h=5, parent=self.screen),
                    Location(22, 24, w=5, h=5, parent=self.screen)]
        finder = LocationOperatorFinder(self.locs_b, below_or_left,
                                        self.locs_a)
        actual = self.gui.find_all(finder)
        self.assertListEqual(actual, expected)


operator_suite = unittest.TestLoader().loadTestsFromTestCase(TestOperators)
all_tests = unittest.TestSuite([operator_suite])
if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(all_tests)
