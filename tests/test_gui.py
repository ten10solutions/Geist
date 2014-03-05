import unittest
from unittest import TestLoader
import numpy as np
from geist import get_platform_backend
from geist.core import GUI, FileGUI, GUICaptureFilter


class TestGUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._backend = get_platform_backend()

    def setUp(self):
        self.gui = GUI(self._backend)

    def test_capture_type(self):
        actual = self.gui.capture()
        self.assertIsInstance(actual, np.ndarray)

    def test_capture_rgb(self):
        actual = self.gui.capture()
        self.assertEqual(actual[0, 0, :].shape, (3,))

    @classmethod
    def tearDownClass(self):
        self._backend.close()


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

    def test_capture_type(self):
        actual = self.gui.capture()
        self.assertIsInstance(actual, np.ndarray)

    def test_capture_rgb(self):
        actual = self.gui.capture()
        self.assertEqual(actual[0, 0, :].shape, (3,))


class TestGUICaptureFilter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._backend = get_platform_backend()

    def setUp(self):
        self.actual_gui = GUI(self._backend)
        self.gui = GUICaptureFilter(self.actual_gui, lambda x: x)

    def test_capture_equality(self):
        actual = self.gui.capture()
        expected = self.actual_gui.capture()
        np.testing.assert_array_equal(actual, expected)

    def test_capture_type(self):
        actual = self.gui.capture()
        self.assertIsInstance(actual, np.ndarray)

    def test_capture_rgb(self):
        actual = self.gui.capture()
        self.assertEqual(actual[0, 0, :].shape, (3,))

    @classmethod
    def tearDownClass(self):
        self._backend.close()


gui_suite = TestLoader().loadTestsFromTestCase(TestGUI)
file_gui_suite = TestLoader().loadTestsFromTestCase(TestFileGUI)
gui_capture_filter_suite = TestLoader().loadTestsFromTestCase(
    TestGUICaptureFilter)

all_gui_suit = unittest.TestSuite([gui_suite, file_gui_suite,
                                   gui_capture_filter_suite])


if __name__ == "__main__":
    unittest.main()
