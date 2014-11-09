import unittest
from geist import Location, LocationList, GUI, FinderInFinder
from geist.backends.fake import GeistFakeBackend


class TestLocationFinderFilter(unittest.TestCase):
    def setUp(self):
        self.gui = GUI(GeistFakeBackend())

    def test_filter(self):
        in_location = self.gui.wait_find_one(Location(10, 10, 100, 100))
        parent_x, parent_y = 40, 50
        child_x, child_y = 100, 17
        finder = FinderInFinder(
            Location(child_x, child_y, 100, 100),
            Location(parent_x, parent_y, 500, 500)
        )
        result = self.gui.wait_find_one(finder)
        self.assertEqual(parent_x + child_x, result.x)
        self.assertEqual(parent_y + child_y, result.y)


location_finder_filter_suite = unittest.TestLoader().loadTestsFromTestCase(
    TestLocationFinderFilter)
all_tests = unittest.TestSuite([location_finder_filter_suite])
if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(all_tests)
