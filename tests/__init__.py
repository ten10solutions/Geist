import logging
import unittest

logger = logging.getLogger('geist.tests')
logging.basicConfig(level=logging.INFO)

from test_filters import all_tests as all_filters
from test_vision import all_tests as all_vision

all_tests = unittest.TestSuite([all_filters, all_vision])
if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(all_tests)
