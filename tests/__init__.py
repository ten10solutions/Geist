import unittest

if __name__ == "__main__":
    all_tests = unittest.TestSuite([])
    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(all_tests)
