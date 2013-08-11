import unittest

from optimizer import Optimizer, WinningProbabilityFunction

GAMES1 = [(1, 2, 1, 1),
          (2, 3, 1, 1),
          (1, 3, 2, 2),
          (3, 2, 3, 0),
          (3, 2, 4, 1)]

GAMES2 = [(1, 2, 1, 1)]

GAMES3 = [(1, 2, 1, 1),
          (1, 2, 2, 0)]

class TestOptimizer(unittest.TestCase):

    def test_probability_func(self):
        f = WinningProbabilityFunction(nparameters=8)

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
        o.load_games(GAMES1)
        self.assertEqual(o.nvars_, 9)

    def test_output_format(self):
        o = Optimizer()
        o.load_games(GAMES1)
        ratings, f = o.random_solution()
        self.assertEqual(len(ratings), 3)
        self.assertEqual(list(sorted(ratings.keys())), [1, 2, 3])
        for player_rating in ratings.values():
            for date, r in player_rating:
                self.assertTrue(1000 < r < 3000)
        self.assertEqual(list(d for d, _ in ratings[1]), [1, 2])
        self.assertEqual(list(d for d, _ in ratings[2]), [1, 3, 4])
        self.assertEqual(list(d for d, _ in ratings[3]), [1, 2, 3, 4])

    def test_objective_single(self):
        o = Optimizer()
        o.load_games(GAMES2)
        v = o.create_vars({1: [(1, 2200)], 2:[(1, 1800)]}, (0, 10))
        (total1, wins_likelihood1, losses_likelihood1, draws_likelihood1,
         regularization1, time_change1, games_change1, func_hard_reg,
         func_soft_reg) = o.objective(v, verbose=True)
        self.assertLess(wins_likelihood1, 0)
        self.assertAlmostEqual(losses_likelihood1, 0)
        self.assertAlmostEqual(draws_likelihood1, 0)
        self.assertTrue(0.01 < regularization1 < 10)
        self.assertEqual(time_change1, 0)
        self.assertEqual(games_change1, 0)
        self.assertTrue(10 < func_hard_reg)
        self.assertTrue(0.01 < func_soft_reg < 10)

        v = o.create_vars({1: [(1, 1800)], 2:[(1, 2200)]}, (0, 10))
        (total2, wins_likelihood2, losses_likelihood2, draws_likelihood2,
         regularization2, _, _, _, _) = o.objective(v, verbose=True)
        self.assertAlmostEqual(regularization1, regularization2)
        self.assertAlmostEqual(losses_likelihood2, 0)
        self.assertAlmostEqual(draws_likelihood2, 0)
        self.assertLess(wins_likelihood2, wins_likelihood1)
        self.assertGreater(total2, total1)

    def test_objective2(self):

    def test_single_game(self):
        o = Optimizer(rating_reg=1E-4, rand_seed=239)
        o.load_games(GAMES2)
        ratings, f, v = o.run()
        _, rating1 = ratings[1][0]
        _, rating2 = ratings[2][0]
        self.assertTrue(100 < rating1 < 4000)
        self.assertTrue(100 < rating2 < 4000)
        self.assertGreater(rating1, rating2)
        self.assertGreater(f.calc(rating1 - rating2), 0.5)

        (total, wins_likelihood, losses_likelihood, draws_likelihood,
         regularization, time_change, games_change, func_hard_reg,
         func_soft_reg) = o.objective(v, verbose=True)

