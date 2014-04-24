import unittest
from geist import Location, LocationList, GUI
from geist.backends.fake import GeistFakeBackend
from geist.filters import (SortingFinder,
                           LocationFinderFilter,
                           SliceFinderFilter)

from ._common import logger as base_logger

logger = base_logger.getChild('filters')


class TestLocationFinderFilter(unittest.TestCase):
    def setUp(self):
        self.gui = GUI(GeistFakeBackend())

    def test_filter(self):
        screen = self.gui.capture_locations()[0]
        self.locs = LocationList([Location(0, 0, w=10, h=10, parent=screen),
                                  Location(0, 8, w=10, h=10, parent=screen),
                                  Location(0, 2, w=10, h=10, parent=screen),
                                  Location(6, 8, w=10, h=10, parent=screen)])
        filter = lambda loc: loc.y == 8
        expected = LocationList([Location(0, 8, w=10, h=10, parent=screen),
                                 Location(6, 8, w=10, h=10, parent=screen)])
        finder = LocationFinderFilter(filter, self.locs)
        actual = self.gui.find_all(finder)
        self.assertListEqual(actual, expected)


class TestSortingFinder(unittest.TestCase):
    def setUp(self):
        self.gui = GUI(GeistFakeBackend())

    def test_sort(self):
        screen = self.gui.capture_locations()[0]
        self.locs = LocationList([Location(0, 0, w=10, h=10, parent=screen),
                                  Location(0, 8, w=10, h=10, parent=screen),
                                  Location(0, 2, w=10, h=10, parent=screen),
                                  Location(6, 8, w=10, h=10, parent=screen)])
        self.key = lambda loc: loc.y
        expected = sorted(self.locs, key=self.key)
        finder = SortingFinder(self.locs, key=self.key)
        actual = self.gui.find_all(finder)
        self.assertListEqual(actual, expected)


class TestSliceFinderFilter(unittest.TestCase):
    def setUp(self):
        self.gui = GUI(GeistFakeBackend())

    def test_index(self):
        screen = self.gui.capture_locations()[0]
        self.locs = LocationList([Location(0, 0, w=10, h=10, parent=screen),
                                  Location(0, 8, w=10, h=10, parent=screen),
                                  Location(0, 2, w=10, h=10, parent=screen),
                                  Location(6, 8, w=10, h=10, parent=screen)])
        expected = LocationList([Location(0, 0, w=10, h=10, parent=screen),
                                 Location(0, 8, w=10, h=10, parent=screen)])
        finder = SliceFinderFilter(self.locs)
        actual = self.gui.find_all(finder[:2])
        self.assertListEqual(actual, expected)

    def test_slice(self):
        screen = self.gui.capture_locations()[0]
        self.locs = LocationList([Location(0, 0, w=10, h=10, parent=screen),
                                  Location(0, 8, w=10, h=10, parent=screen),
                                  Location(0, 2, w=10, h=10, parent=screen),
                                  Location(6, 8, w=10, h=10, parent=screen)])
        expected = LocationList([Location(0, 0, w=10, h=10, parent=screen),
                                 Location(0, 8, w=10, h=10, parent=screen)])
        finder = SliceFinderFilter(self.locs)
        actual = self.gui.find_all(finder[slice(0, 2)])
        self.assertListEqual(actual, expected)


filter_suite = unittest.TestLoader().loadTestsFromTestCase(
    TestLocationFinderFilter)
sort_suite = unittest.TestLoader().loadTestsFromTestCase(TestSortingFinder)
slice_suite = unittest.TestLoader().loadTestsFromTestCase(
    TestSliceFinderFilter)
all_tests = unittest.TestSuite([sort_suite, filter_suite, slice_suite])
if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(all_tests)
