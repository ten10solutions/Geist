import numpy as np
from numpy.testing import assert_array_equal
from geist.similar_images import is_similar, find_similar_in_repo
from geist import GUI, DirectoryRepo
from geist.pyplot import Viewer
from geist.backends.fake import GeistFakeBackend
import unittest

# use same test cases as for testing vision, but need a non binary test as well
class TestSimilarity(unittest.TestCase):
    def setUp(self):
        self.repo = DirectoryRepo('test_repo')
        self.gui = GUI(GeistFakeBackend())
        self.V = Viewer(self.gui, self.repo)
        # first need to save some images to repo
        self.image = np.array([[0, 0, 0, 0, 0],
                          [0, 0, 0, 1, 0],
                          [0, 0, 1, 0, 0],
                          [0, 1, 0, 0, 0],
                          [0, 0, 0, 0, 0]])
        self.image2 = np.array([[0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 1, 0, 0, 0],
                          [0, 0, 1, 0, 0, 0, 0],
                          [0, 1, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0]])
        self.image3 = np.array([[[255,0,0],[240,10,10],[0,255,0],[0,0,255]]], dtype=np.int32)
        self.V._save('test_file_1', self.image, force=True)
        self.V._save('test_file_2', self.image2, force=True)
        self.V._save('test_file_3', self.image3, force=True)
            
    def test_no_match(self):
        blank = np.zeros((100, 100))
        template = np.array([[0, 1], [1, 0]])

        expected = []
        result = is_similar(template, blank)
        self.assertFalse(result)

    def test_match(self):
        image = np.array([[0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 1, 0],
                          [0, 0, 0, 0, 0, 1, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 1, 0, 0, 0, 0, 0],
                          [0, 1, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0]])
        template = np.array([[0, 1], [1, 0]])
        result = is_similar(template, image)
        self.assertEqual(result, "matches exist- size different")
        
    def test_similar_size(self):
        template = np.array([[0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 1, 0, 0],
                          [0, 0, 1, 0, 0, 0],
                          [0, 1, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0]])
        result = is_similar(template, self.image, size_tolerance=0.2)
        self.assertTrue(result)
        
    def test_colour(self):
        result = is_similar(self.image3, self.image3)
        self.assertTrue(result)
                
    def test_colour_size_different(self):
        template = np.array([[[255,0,0],[240,10,10]]], dtype=np.int32)
        result = is_similar(template, self.image3)
        self.assertEqual(result, "matches exist- size different")
        
    def test_find_similar_in_repo_similar(self):
        similar, different_size, no_match = find_similar_in_repo(self.image, self.repo, size_tolerance=0.2)
        self.assertListEqual(similar, ['test_file_1'])

        
    def test_find_similar_in_repo_different_size(self):
        similar, different_size, no_match = find_similar_in_repo(self.image, self.repo, size_tolerance=0.2)
        self.assertListEqual(different_size, ['test_file_2'])
        
    def test_find_similar_in_repo_similar_no_match(self):
        similar, different_size, no_match = find_similar_in_repo(self.image, self.repo, size_tolerance=0.2)
        self.assertListEqual(no_match, ['test_file_3'])
        
    def test_find_similar_in_repo_similar_no_match_2(self):
        image = np.array([[1,1],[1,1]])
        similar, different_size, no_match = find_similar_in_repo(image, self.repo, size_tolerance=0.2)
        self.assertListEqual(sorted(no_match), sorted(['test_file_1', 'test_file_2', 'test_file_3']))

    def tearDown(self):
        if 'test_file_1' in self.repo.entries:
            del self.repo['test_file_1']  
        if 'test_file_2' in self.repo.entries:
            del self.repo['test_file_2'] 
        if 'test_file_3' in self.repo.entries:
            del self.repo['test_file_3'] 
        

similar_suite = unittest.TestLoader().loadTestsFromTestCase(TestSimilarity)
all_tests = unittest.TestSuite([similar_suite])
if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(all_tests)
