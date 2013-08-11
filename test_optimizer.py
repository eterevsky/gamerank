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

GAMES3A = [(1, 2, 1, 1),
           (1, 2, 100, 0)]

GAMES4 = [(1, 2, 1, 2),
          (2, 1, 1, 2)]


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
            for r in player_rating.values():
                self.assertTrue(1000 < r < 3000)
        self.assertEqual(list(sorted(ratings[1].keys())), [1, 2])
        self.assertEqual(list(sorted(ratings[2].keys())), [1, 3, 4])
        self.assertEqual(list(sorted(ratings[3].keys())), [1, 2, 3, 4])

    def test_objective_single(self):
        o = Optimizer()
        o.load_games(GAMES2)
        v = o.create_vars({1: {1: 2200}, 2: {1: 1800}}, (0, 10))
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

        v = o.create_vars({1: {1: 1800}, 2: {1: 2200}}, (0, 10))
        (total2, wins_likelihood2, losses_likelihood2, draws_likelihood2,
         regularization2, _, _, _, _) = o.objective(v, verbose=True)
        self.assertAlmostEqual(regularization1, regularization2)
        self.assertAlmostEqual(losses_likelihood2, 0)
        self.assertAlmostEqual(draws_likelihood2, 0)
        self.assertLess(wins_likelihood2, wins_likelihood1)
        self.assertGreater(total2, total1)

    def test_single_game(self):
        o = Optimizer(rating_reg=1E-4, rand_seed=239)
        o.load_games(GAMES2)
        ratings, f, v = o.run()
        self.assertTrue(100 < ratings[1][1] < 4000)
        self.assertTrue(100 < ratings[2][1] < 4000)
        self.assertGreater(ratings[1][1], ratings[2][1])
        self.assertGreater(f.calc(ratings[1][1] - ratings[2][1]), 0.5)

        (total, wins_likelihood, losses_likelihood, draws_likelihood,
         regularization, time_change, games_change, func_hard_reg,
         func_soft_reg) = o.objective(v, verbose=True)

    def test_objective_time_reg(self):
        o = Optimizer(rating_reg=1E-4, rand_seed=239, time_delta=1.0,
                      games_delta=0.0)
        o.load_games(GAMES3)
        v = o.create_vars({1: {1: 2200, 2: 1800}, 2: {1: 1800, 2: 2200}},
                          (0, 10))
        (total1, wins_likelihood1, losses_likelihood1, draws_likelihood1,
         regularization1, time_change1, games_change1,
         _, _) = o.objective(v, verbose=True)
        self.assertLess(wins_likelihood1, 0)
        self.assertLess(losses_likelihood1, 0)
        self.assertAlmostEqual(draws_likelihood1, 0)
        self.assertTrue(0.01 < regularization1 < 10)
        self.assertTrue(1 < time_change1 < 100)
        self.assertTrue(1 < games_change1 < 100)

    def test_time_regularization(self):
        o = Optimizer(rating_reg=1E-4, rand_seed=239, time_delta=0.01,
                      games_delta=0.0)
        o.load_games(GAMES3)
        rating, f, v = o.run()

        (total1, _, _, _, _, time_change1,
         _, func_hard_reg, _) = o.objective(v, verbose=True)
        self.assertLess(func_hard_reg, 1)
        self.assertGreater(time_change1, 0.1)

        self.assertGreater(rating[1][1], rating[1][2])
        self.assertLess(rating[2][1], rating[2][2])
        self.assertGreater(rating[1][1], rating[2][1])
        self.assertLess(rating[1][2], rating[2][2])
        prob1 = f.calc(rating[1][1] - rating[2][1])
        self.assertGreater(prob1, 0.6)
        prob2 = f.calc(rating[1][2] - rating[2][2])
        self.assertLess(prob2, 0.4)

        o.load_games(GAMES3A)
        ratinga, f, v = o.run()

        (total2, _, _, _, _, time_change2, _, _, _) = o.objective(v, verbose=True)
        self.assertLess(time_change2, time_change1)
        self.assertGreater(abs(ratinga[1][100] - ratinga[1][1]),
                           abs(rating[1][2] - rating[1][1]))
        self.assertGreater(abs(ratinga[2][100] - ratinga[2][1]),
                           abs(rating[2][2] - rating[2][1]))
        self.assertGreater(f.calc(ratinga[1][1] - ratinga[2][1]), prob1)
        self.assertLess(f.calc(ratinga[1][100] - ratinga[2][100]), prob2)


    def test_draw(self):
        o = Optimizer(rand_seed=239)
        o.load_games(GAMES4)
        rating, f, _ = o.run()

        self.assertAlmostEqual(f.calc(0), 0.5, 3)
        self.assertLess(abs(rating[1][1] - rating[2][1]), 5)

    def test_games1(self):
        o = Optimizer(rand_seed=239, time_delta=0.01, games_delta=0.01)
        o.load_games(GAMES1)
        rating, f, _ = o.run()

        self.assertGreater(rating[1][1], rating[2][1])
        self.assertGreater(rating[2][1], rating[3][1])
        self.assertLess(rating[1][2], rating[1][1])
        self.assertGreater(rating[3][4], rating[3][3])
