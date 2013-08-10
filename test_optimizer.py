import unittest

from optimizer import Optimizer, WinningProbabilityFunction

GAMES = [(1, 2, 1, 1),
         (2, 3, 1, 1),
         (1, 3, 2, 2),
         (3, 2, 3, 0),
         (3, 2, 3, 1)]

class TestOptimizer(unittest.TestCase):

    def test_probability_func(self):
        f = WinningProbabilityFunction(n_points=4, steps_in_200=2)

        f.reset_from_vars([1] * 8)
        self.assertAlmostEqual(f.calc(-500), 0)
        self.assertAlmostEqual(f.calc(-400), 0)
        self.assertTrue(0 < f.calc(-350) < 0.125)
        self.assertAlmostEqual(f.calc(-300), 0.125)
        self.assertAlmostEqual(f.calc(0), 0.5)
        self.assertTrue(0.5 < f.calc(50) < 0.625)
        self.assertAlmostEqual(f.calc(100), 0.625)
        self.assertAlmostEqual(f.calc(600), 1)

        arr = f.calc_vector([-500, -400, 400])
        self.assertEqual(len(arr), 3)
        self.assertAlmostEqual(arr[0], 0)
        self.assertAlmostEqual(arr[1], 0)
        self.assertAlmostEqual(arr[2], 1)

        self.assertGreater(f.hard_regularization(), 0)
        self.assertAlmostEqual(f.soft_regularization(), 0)

        f.reset_from_vars([0, 0.375, 0, 0, 0, 0.5, 0.125, 0])
        self.assertAlmostEqual(f.calc(-300), 0)
        self.assertAlmostEqual(f.calc(-200), 0.375)

        self.assertAlmostEqual(f.hard_regularization(), 0)
        self.assertGreater(f.soft_regularization(), 0)

    def test_prepare_data(self):
        o = Optimizer()
        o.load_games(GAMES)
        self.assertEqual(o.nvars_, 9)
