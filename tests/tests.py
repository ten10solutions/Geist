from __future__ import division, absolute_import, print_function
import unittest

from test_filters import all_tests as all_filters
from test_vision import all_tests as all_vision
from test_operators import all_tests as all_operators
from test_replay import all_tests as all_replay

all_tests = unittest.TestSuite(
    [all_filters, all_vision, all_operators, all_replay]
)
if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(all_tests)
