import unittest
import pkg_resources
import numpy as np
from geist import GUI, BinaryRegionFinder, Location, DirectoryRepo
from geist.backends.fake import GeistFakeBackend
from geist.pyplot import Viewer


class TestViewer(unittest.TestCase):
    def setUp(self):
        self.repo = DirectoryRepo('test_repo')
        self.gui = GUI(GeistFakeBackend(image=np.array([[[255,0,0],[240,10,10],[0,255,0],[0,0,255]]])))
        self.V = Viewer(self.gui, self.repo)
        self.screen = self.gui.capture_locations()[0]
        self.red = np.array([[[255,0,0]]])
        self.more_reds = np.array([[[255,0,0],[240,10,10]]])
    
    
    def test_get_colour(self):
        red = self.V._get_colour(self.red)
        result = self.gui.find_all(BinaryRegionFinder(red))
        expected = [Location(0,0, w=1, h=1, parent=self.screen)]
        self.assertListEqual(result, expected)
    
    
    def test_get_colour_range(self):
        reds = self.V._get_colour(self.more_reds)
        result = self.gui.find_all(BinaryRegionFinder(reds))
        expected = [Location(0,0, w=2, h=1, parent=self.screen)]
        self.assertListEqual(result, expected)
        
    
viewer_suite = unittest.TestLoader().loadTestsFromTestCase(TestViewer)
all_tests = unittest.TestSuite([viewer_suite])
if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(all_tests)
