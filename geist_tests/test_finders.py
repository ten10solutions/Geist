import unittest
from geist import Location, LocationList, GUI, FinderInFinder
from geist.backends.fake import GeistFakeBackend
from geist.responsivefinders import LocationChangeFinder, StopChangingFinder, ClickingFinder
from geist_tests.test_mouse import GeistMouseBackend
import numpy as np


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


class TestResponsiveFinders(unittest.TestCase):
    def setUp(self):
        # typically images are rgb, and fake backend expects this
        self.location_image = np.array([[[1],[1]],[[1],[1]]], dtype=int)
        self.location = Location(0,0,2,2,image=self.location_image)
        
    # make a location with an image to initialise finder
    # then use location with a different image to call with find
    def test_LocationChangeFinder(self):
        finder = LocationChangeFinder(self.location)
        new_location_image = np.array([[[0],[0]],[[0],[0]]])
        new_location = Location(0,0,2,2,image=new_location_image)
        location_found = list(finder.find(new_location))[0]
        self.assertTrue(np.array_equal(location_found.image, new_location.image))
        
    # doesn't distinguish between stopping changing and never changing
    # in practise can check it changes with location change finder
    # use with gui wait find one for looping, so in this test, no looping happens- returns nothing
    def test_StopChangingFinder(self):
        finder = StopChangingFinder(self.location)
        finder.period = 1
        location_found = list(finder.find(self.location))
        self.assertEquals(location_found, [])
        
    # set it up with one image, then look using a location with a different image
    def test_nontrivial_StopChangingFinder(self):
        backend = GeistFakeBackend(image=np.array([[[0],[0]],[[0],[0]]]))
        gui = GUI(backend)
        finder = StopChangingFinder(self.location)
        #backend.image = np.array([[[0],[0]],[[0],[0]]]) 
        finder.period = 1
        location_found = gui.wait_find_one(finder)
        self.assertTrue(np.array_equal(location_found.image, backend.image))
        
    def test_ClickingFinder(self):
        backend = GeistMouseBackend()
        gui = GUI(backend)
        finder = ClickingFinder(self.location, gui)
        # things only happen when generator consumed
        list(finder.find(self.location))
        self.assertTrue(backend.button_up_pressed)
        self.assertTrue(backend.button_down_pressed)
        self.assertIn((0,0), backend.list_of_points)
