import unittest
from unittest import TestLoader
import numpy as np
from geist import get_platform_backend
from geist.core import GUI, FileGUI


class TestGUI(unittest.TestCase):
    def setUp(self):
        self._backend = get_platform_backend()
        self.gui = GUI(self._backend)

    def test_capture_type(self):
        actual = self.gui.capture()
        self.assertIsInstance(actual, np.ndarray)

    def test_capture_rgb(self):
        actual = self.gui.capture()
        self.assertEqual(actual[0, 0, :].shape, (3,))


class TestFileGUI(unittest.TestCase):
    def setUp(self):
        self._backend = get_platform_backend()
        self.filename = "test.npy"
        self.image = np.load("test.npy")
        self.gui = FileGUI(self.filename, self._backend)

    def test_capture(self):
        actual = self.gui.capture()
        expected = self.image
        np.testing.assert_array_equal(actual, expected)


gui_suite = TestLoader().loadTestsFromTestCase(TestGUI)
file_gui_suite = TestLoader().loadTestsFromTestCase(TestFileGUI)
all_gui_suit = unittest.TestSuite([gui_suite, file_gui_suite])


if __name__ == "__main__":
    unittest.main()
