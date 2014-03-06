import unittest
from test_gui import all_gui_suit

all_tests = unittest.TestSuite([all_gui_suit])

if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(all_tests)
