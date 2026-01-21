import unittest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.metrics import calculate_pass_at_k, calculate_pass_all_k

class TestMetrics(unittest.TestCase):
    
    def test_pass_at_k_basic(self):
        # n=10, c=5, k=1
        # Expect: 5/10 = 0.5
        self.assertAlmostEqual(calculate_pass_at_k(10, 5, 1), 0.5)
        
    def test_pass_at_k_perfect(self):
        # n=10, c=10, k=5
        # Expect: 1.0
        self.assertAlmostEqual(calculate_pass_at_k(10, 10, 5), 1.0)
        
    def test_pass_at_k_zero(self):
        # n=10, c=0, k=1
        # Expect: 0.0
        self.assertAlmostEqual(calculate_pass_at_k(10, 0, 1), 0.0)
        
    def test_pass_at_k_formula(self):
        # n=4, c=2 (correct: A, B; incorrect: C, D)
        # k=2
        # Total combos of 2: AB, AC, AD, BC, BD, CD (6)
        # Incorrect combos of 2: CD (1)
        # Correct (at least one): 5/6
        # Formula: 1 - (2C2 / 4C2) = 1 - (1/6) = 5/6
        self.assertAlmostEqual(calculate_pass_at_k(4, 2, 2), 5/6)

    def test_pass_at_k_insufficient_samples(self):
        # n=5, k=10
        self.assertEqual(calculate_pass_at_k(5, 5, 10), 0.0)

    def test_pass_all_k_basic(self):
        # n=4, c=2 (correct: A, B; incorrect: C, D)
        # k=2
        # Total combos of 2: 6
        # All correct combos: AB (1)
        # Expect: 1/6
        self.assertAlmostEqual(calculate_pass_all_k(4, 2, 2), 1/6)

    def test_pass_all_k_perfect(self):
        # n=10, c=10, k=5
        self.assertAlmostEqual(calculate_pass_all_k(10, 10, 5), 1.0)

    def test_pass_all_k_impossible(self):
        # n=10, c=2, k=3
        # Can't pick 3 correct if only 2 are correct
        self.assertEqual(calculate_pass_all_k(10, 2, 3), 0.0)

if __name__ == '__main__':
    unittest.main()
