import numpy as np
import unittest

from math import log
from optimizer import Optimizer, LogisticProbabilityFunction, convert_rating_diff

GAMES1 = [(1, 2, 1, 1),
          (2, 3, 1, 1),
          (1, 3, 2, 2),
          (3, 2, 3, 0),
          (3, 2, 4, 1)]


def derivative(f, x, dx=1E-6):
    return (f(x + dx) - f(x - dx)) / (2*dx)


class TestOptimizer(unittest.TestCase):

    def test_func_sum_log(self):
        a = np.array([-0.5, 1, 2])
        f = LogisticProbabilityFunction()
        f.reset_from_vars([0, 400])

        s1 = 0
        for x in a:
            s1 += log(f.calc(x))

        s2 = 0
        for x in a:
            s2 += f.calc_log(x)

        s3 = f.sum_log(a)

        self.assertAlmostEqual(s1, s2)
        self.assertAlmostEqual(s1, s3)

        s1 = 0
        for x in a:
            s1 += log(1 - f.calc(x))

        s2 = f.sum_log1m(a)

        self.assertAlmostEqual(s1, s2)

    def test_func_deriv(self):
        f = LogisticProbabilityFunction()
        f.reset_from_vars([0.5, 0])
        self.assertAlmostEqual(derivative(f.calc, 0.6), f.deriv(0.6), 5)

        def freg(mu, ls):
            save = [f.mu, f.ls]
            f.reset_from_vars([mu, ls])
            res = f.hard_reg(), f.soft_reg()
            f.reset_from_vars(save)
            return res

        fhard_by_mu = lambda mu: freg(mu, 0)[0]
        fsoft_by_mu = lambda mu: freg(mu, 0)[1]
        fhard_by_s = lambda s: freg(0.5, s)[0]
        fsoft_by_s = lambda s: freg(0.5, s)[1]

        self.assertAlmostEqual(derivative(fhard_by_mu, 0.5), f.hard_reg_grad()[0], 5)
        self.assertAlmostEqual(derivative(fhard_by_s, 0), f.hard_reg_grad()[1], 5)
        self.assertAlmostEqual(derivative(fsoft_by_mu, 0.5), f.soft_reg_grad()[0], 5)
        self.assertAlmostEqual(derivative(fsoft_by_s, 0), f.soft_reg_grad()[1], 5)

        def fp(x, mu, ls):
            save = [f.mu, f.ls]
            f.reset_from_vars([mu, ls])
            res = f.calc(x)
            f.reset_from_vars(save)
            return res

        f_by_mu = lambda mu: fp(10, mu, 0)
        f_by_s = lambda s: fp(10, 0.5, s)

        self.assertAlmostEqual(derivative(f_by_mu, 0.5), f.params_grad(10)[0])
        self.assertAlmostEqual(derivative(f_by_s, 0), f.params_grad(10)[1])


    def test_prepare_data(self):
        o = Optimizer()
        o.load_games(GAMES1)
        self.assertEqual(o.nrating_vars_, 9)

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

    def test_objective_single_game(self):
        o = Optimizer()
        o.load_games([(1, 2, 1, 1)])
        v1 = o.create_vars({1: {1: 2200}, 2: {1: 1800}}, [0, -1.01])
        v2 = o.create_vars({1: {1: 2200}, 2: {1: 2200}}, [0, -1.01])
        v3 = o.create_vars({1: {1: 1800}, 2: {1: 2200}}, [0, -1.01])

        (total1, likelihood1, regularization1, smoothness1,
         func_hard_reg, _) = o.objective(v1, verbose=True)
        self.assertLess(likelihood1, 0)
        self.assertTrue(1E-6 < regularization1 < 1)
        self.assertEqual(smoothness1, 0)
        self.assertTrue(func_hard_reg < 1)

        (total2, likelihood2, regularization2, _, _, _) = o.objective(
            v2, verbose=True)
        self.assertLess(likelihood2, likelihood1)

        (total3, likelihood3, regularization3, _, _, _) = o.objective(
            v3, verbose=True)
        self.assertAlmostEqual(regularization1, regularization3)


        self.assertLess(total1 / total2, 0.9)
        self.assertLess(total2 / total3, 0.9)

    def test_gradient(self):
        o = Optimizer(func_hard_reg=0, func_soft_reg=0, time_delta=0,
                      rating_reg=0)
        o.load_games([(1, 2, 1, 1)])
        v = o.create_vars({1: {1: 2200}, 2: {1: 1800}}, (0, -1.01))

        def o0(x):
             save_x = v[0]
             v[0] = x
             res = o.objective(v)
             v[0] = save_x
             return res

        def o1(x):
             save_x = v[1]
             v[1] = x
             res = o.objective(v)
             v[1] = save_x
             return res

        self.assertAlmostEqual(derivative(o0, v[0]), o.gradient(v)[0])
        self.assertAlmostEqual(derivative(o1, v[1]), o.gradient(v)[1])

    def test_single_game(self):
        o = Optimizer(rand_seed=239)
        o.load_games([(1, 2, 1, 1)])
        ratings, f, v = o.run()
        (total, likelihood, regularization, smoothness,
         func_hard_reg, func_soft_reg) = o.objective(v, verbose=True)
        self.assertTrue(100 < ratings[1][1] < 4000)
        self.assertTrue(100 < ratings[2][1] < 4000)
        self.assertGreater(
            f.calc(convert_rating_diff(ratings[1][1] - ratings[2][1])), 0.5)
        self.assertGreater(ratings[1][1], ratings[2][1])

        total = o.objective(v)

    def test_objective_time_reg(self):
        o = Optimizer(rand_seed=239)
        o.load_games([(1, 2, 1, 1), (1, 2, 2, 0)])
        v = o.create_vars({1: {1: 2200, 2: 1800}, 2: {1: 1800, 2: 2200}},
                          (0, -1.01))
        (total, likelihood, regularization, _, _, _) = o.objective(
             v, verbose=True)
        self.assertLess(likelihood, 0)
        self.assertTrue(1E-6 < regularization < 1)

    def test_time_regularization(self):
        o = Optimizer(rand_seed=239)
        o.load_games([(1, 2, 1, 1), (2, 1, 1, 0), (1, 2, 2, 0), (2, 1, 2, 1)])
        rating, f, v = o.run()

        (total1, _, reg, smoothness1, func_hard_reg,
         func_soft_reg) = o.objective(v, verbose=True)
        self.assertLess(func_hard_reg, 1)
        self.assertGreater(smoothness1, 0.001)

        self.assertGreater(rating[1][1], rating[1][2])
        self.assertLess(rating[2][1], rating[2][2])
        self.assertGreater(rating[1][1], rating[2][1])
        self.assertLess(rating[1][2], rating[2][2])
        prob1 = f.calc(convert_rating_diff(rating[1][1] - rating[2][1]))
        self.assertGreater(prob1, 0.51)
        prob2 = f.calc(convert_rating_diff(rating[1][2] - rating[2][2]))
        self.assertLess(prob2, 0.49)

    def test_objective_symmetric_wins(self):
        o = Optimizer(rating_reg=0)
        o.load_games([(1, 2, 1, 1), (2, 1, 1, 1)])

        v1 = o.create_vars({1: {1: 2200}, 2: {1: 1800}}, [0, -1.01])
        v2 = o.create_vars({1: {1: 2000}, 2: {1: 2000}}, [0, -1.01])
        v3 = o.create_vars({1: {1: 1800}, 2: {1: 2200}}, [0, -1.01])

        self.assertLess(o.objective(v2) / o.objective(v1), 0.9)
        self.assertLess(o.objective(v2) / o.objective(v3), 0.9)

    def test_symmetric_wins(self):
        o = Optimizer(rand_seed=239)
        o.load_games([(1, 2, 1, 1), (1, 2, 1, 0), (2, 1, 1, 1), (2, 1, 1, 0)])
        rating, f, v = o.run(method='Newton-CG')

        self.assertAlmostEqual(
            f.calc(convert_rating_diff(rating[1][1] - rating[2][1])), 0.5, 2)
        self.assertLess(abs(rating[1][1] - rating[2][1]), 5)

    def test_objective_draw(self):
        o = Optimizer(rating_reg=0)
        o.load_games([(1, 2, 1, 2), (2, 1, 1, 2)])

        v1 = o.create_vars({1: {1: 2200}, 2: {1: 1800}}, [0, -1.01])
        v2 = o.create_vars({1: {1: 2000}, 2: {1: 2000}}, [0, -1.01])
        v3 = o.create_vars({1: {1: 1800}, 2: {1: 2200}}, [0, -1.01])

        self.assertLess(o.objective(v2), o.objective(v1))
        self.assertLess(o.objective(v2), o.objective(v3))

    def test_draw(self):
        o = Optimizer(rand_seed=239)
        o.load_games([(1, 2, 1, 2), (2, 1, 1, 2)])
        rating, f, v = o.run(method='cg')

        self.assertAlmostEqual(f.calc(0), 0.5, 3)
        self.assertAlmostEqual(
            f.calc(convert_rating_diff(rating[1][1] - rating[2][1])), 0.5, 2)
        self.assertLess(abs(rating[1][1] - rating[2][1]), 5)

    def test_gradient_games1(self):
        o = Optimizer(rand_seed=239, time_delta=0.01, func_hard_reg=0,
                      func_soft_reg=0)
        o.load_games(GAMES1)
        v = o.init()

        grad = o.gradient(v)

        for i in range(len(v)):
            def ocomp(x):
                save_x = v[i]
                v[i] = x
                res = o.objective(v)
                v[i] = save_x
                return res
            self.assertAlmostEqual(derivative(ocomp, v[i]), grad[i])

    def test_games1(self):
        o = Optimizer(rand_seed=239)
        o.load_games(GAMES1)
        rating, f, _ = o.run(method='newton-cg')
