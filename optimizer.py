from math import ceil, cosh, exp, log, tanh

try:
    import numexpr as ne
except ImportError:
    ne = None

import numpy as np
from random import random, seed
import scipy.sparse as sparse
import sys
import time


try:
  from scipy.optimize import minimize
except ImportError:
  from scipy.optimize import fmin, fmin_powell, fmin_cg, fmin_bfgs, fmin_ncg, fmin_l_bfgs_b

  def minimize(func, x0, method='CG', options=None, jac=None, callback=None):
      method = method.lower()

      if 'disp' in options:
          disp = options['disp']
      else:
          disp = False

      if 'maxiter' in options:
          maxiter = options['maxiter']
      else:
          maxiter = None

      if method == 'nelder-mead':
          x = fmin(func=func, x0=x0, disp=disp, maxiter=maxiter, callback=callback)
      elif method == 'powell':
          x = fmin_powell(func=func, x0=x0, disp=disp, maxiter=maxiter, callback=callback)
      elif method == 'cg':
          x = fmin_cg(f=func, x0=x0, fprime=jac, disp=disp, maxiter=maxiter, callback=callback)
      elif method == 'bfgs':
          x = fmin_bfgs(f=func, x0=x0, fprime=jac, disp=disp, maxiter=maxiter, callback=callback)
      elif method == 'l-bfgs-b':
          d = ceil(1000000 / len(x0))
          print(d)
          x, _, _ = fmin_l_bfgs_b(func=func, x0=x0, fprime=jac, disp=(d if disp else 0))
      elif method == 'newton-cg':
          x = fmin_ncg(f=func, x0=x0, fprime=jac, disp=disp, maxiter=maxiter, callback=callback)

      class Result(object):
          def __init__(self, x):
              self.x = x

      return Result(x)

if ne:
    ne.set_num_threads(32)


def sech(x):
    ee = np.exp(-abs(x))
    return 2 * ee / (1 + ee*ee)


if ne:
    def sech2(x):
        return ne.evaluate("1 / cosh(x)**2")
else:
    def sech2(x):
        ee = np.exp(-abs(x))
        return (2 * ee / (1 + ee*ee)) ** 2


def convert_rating(x):
    return x / 1000.0 - 1.0


def convert_rating_diff(d):
    return d / 1000.0


class LogisticProbabilityFunction(object):
    def __init__(self):
        self.mu = 0
        self.ls = 0
        self.s = 1

    def init(self):
        return [0, -1.0]

    def reset_from_vars(self, var):
        self.mu, self.ls = var[0], var[1]
        if self.ls > 50:
            self.s = 1E20
        else:
            self.s = exp(self.ls)
        if self.s < 1E-20:
            self.s = 1E-20

    def __str__(self):
        return "0.5 + 0.5 * tanh((x + {}) / {})".format(-self.mu, self.s)

    def calc(self, x):
        return 0.5 + 0.5 * tanh((x - self.mu) / self.s)

    if ne:
        def calc_vector(self, x):
            mu = self.mu
            s = self.s
            return ne.evaluate('0.5 + 0.5 * tanh((x - mu) / s)')

        def deriv(self, x):
            s = self.s
            mu = self.mu
            return ne.evaluate('0.5 / (s * cosh((x - mu) / s) ** 2)')
    else:
        def calc_vector(self, x):
            return 0.5 + 0.5 * np.tanh((x - self.mu) / self.s)

        def deriv(self, x):
            return sech2((x - self.mu) / self.s) / (2 * self.s)

    def calc_log(self, x):
        y = 2 * (x - self.mu) / self.s
        if y > 0:
            return -log(1 + exp(-y))
        else:
            return y - log(exp(y) + 1)

    def calc_log_vector(self, vx):
        return map(self.calc_log, vx)

    def sum_log(self, vx):
        vy = 2 * (vx - self.mu) / self.s

        pos_idx = vy > 0
        vpos = vy[pos_idx]
        vneg = vy[~pos_idx]

        return (-np.sum(np.log(1 + np.exp(-vpos))) +
                np.sum(vneg - np.log(np.exp(vneg) + 1)))

    def calc_log1m(self, x):
        """Calculate log(1 - f(x))"""
        y = 2 * (x - self.mu) / self.s
        if y > 0:
            return -y - log(1 + exp(-y))
        else:
            return -log(1 + exp(y))

    def calc_log1m_vector(self, vx):
        return map(self.calc_log1m, vx)

    def sum_log1m(self, vx):
        vy = 2 * (vx - self.mu) / self.s

        vpos = -vy[vy > 0]
        vneg = vy[vy <= 0]

        return (np.sum(vpos - np.log(1 + np.exp(vpos))) +
                np.sum(-np.log(1 + np.exp(vneg))))

    def hard_reg(self):
        elo_norm = self.calc(0.2) - self.calc(-0.2)
        return (elo_norm - 0.5)**2

    def hard_reg_grad(self):
        arg1 = (0.2 - self.mu) / self.s
        arg2 = (-0.2 - self.mu) / self.s
        return (0.5 * (tanh(arg1) - tanh(arg2) - 1) *
                (sech2(arg1) * np.array([-1/self.s, -arg1]) -
                 sech2(arg2) * np.array([-1/self.s, -arg2])))

    def soft_reg(self):
        return self.mu**2 + (self.ls + 1)**2

    def soft_reg_grad(self):
        return np.array([2*self.mu, 2*(self.ls + 1)])

    def params_grad(self, x):
        d = sech2((x - self.mu) / self.s)
        return d * np.array([-1 / (2 * self.s),
                            (self.mu - x) / (2 * self.s)])

    def params_grad_vector(self, x):
        y = (x - self.mu) / self.s
        d = sech2(y)
        a = np.array([[-1 / (2*self.s)], [-0.5]]) * np.ones(len(y))
        a[1] *= y
        return a * d
        # return np.array([-d / (2 * self.s),
        #                  d * (self.mu - x) / (2 * self.s)])


class Optimizer(object):
    def __init__(self, disp=False, func_hard_reg=50.0, func_soft_reg=1E-5,
                 time_delta=100.0, rating_reg=10.0, rand_seed=None):
        seed(rand_seed)
        self.f = LogisticProbabilityFunction()
        self.disp = disp
        self.func_hard_reg = func_hard_reg
        self.func_soft_reg = func_soft_reg
        self.time_delta = time_delta
        self.rating_reg = rating_reg * 1E-6

        self.objective_calls = 0
        self.gradient_calls = 0

    def load_games(self, results):
        """Load the list of game results.

        Args:
            games: list of tuples (player1, player2, date, result)
            Result is 0 for black victory, 1 for white victory, 2 for draw.
        """
        # Sort games by result: losses, wins, draws.
        self.games_ = list(sorted(results, key=lambda g: g[3]))
        # Fill self.wins_slice_ and so on.
        self.create_game_result_slices_(self.games_)

        # player -> date -> games count
        player_date_games_count = self.generate_player_date_games_()

        self.var_player_date_, player_date_var = self.index_rating_vars_(
            player_date_games_count)
        self.nrating_vars_ = len(self.var_player_date_)

        self.time_delta_vector_ = self.generate_time_delta_(
            player_date_games_count)

        self.grad_by_game_m_ = self.create_grad_by_game_(player_date_var)

    def create_grad_by_game_(self, player_date_var):
        self.games_player1_var_ = []
        self.games_player2_var_ = []
        for player1, player2, date, _ in self.games_:
            self.games_player1_var_.append(player_date_var[(player1, date)])
            self.games_player2_var_.append(player_date_var[(player2, date)])

        self.games_player1_var_ = np.array(self.games_player1_var_)
        self.games_player2_var_ = np.array(self.games_player2_var_)

        m = sparse.lil_matrix(
            (self.nrating_vars_, len(self.games_)), dtype=np.int8)

        for i in range(len(self.games_)):
            m[self.games_player1_var_[i], i] = 1
            m[self.games_player2_var_[i], i] = -1

        return m.tocsr()

    def create_game_result_slices_(self, games):
        last_loss = -1
        last_win = -1
        for i in range(len(games)):
            if games[i][3] == 0:
                last_loss = i
                last_win = i
            elif games[i][3] == 1:
                last_win = i
        self.losses_slice_ = slice(0, last_loss + 1)
        self.wins_slice_ = slice(last_loss + 1, last_win + 1)
        self.draws_slice_ = slice(last_win + 1, len(self.games_))

    def generate_player_date_games_(self):
        player_date_games = {}
        for player1, player2, date, _ in self.games_:
            if player1 not in player_date_games:
                player_date_games[player1] = {}
            if date not in player_date_games[player1]:
                player_date_games[player1][date] = 0
            player_date_games[player1][date] += 1

            if player2 not in player_date_games:
                player_date_games[player2] = {}
            if date not in player_date_games[player2]:
                player_date_games[player2][date] = 0
            player_date_games[player2][date] += 1

        return player_date_games

    def index_rating_vars_(self, player_date_games_count):
        var_player_date = []
        player_date_var = {}
        for player, date_games_count in player_date_games_count.items():
            for date in sorted(date_games_count.keys()):
                player_date_var[(player, date)] = len(var_player_date)
                var_player_date.append((player, date))
        return var_player_date, player_date_var

    def generate_time_delta_(self, player_date_games):
        """Generate a table of coefficients to rating changes.

        1 / (difference in days for subsequent ratings) +
        1 / (the number of games between)

        TODO: Tune coefficients of each part.
        """

        delta_vector = []
        last_player, last_date = self.var_player_date_[0]
        last_games = player_date_games[last_player][last_date]
        for player, date in self.var_player_date_[1:]:
            games = player_date_games[player][date]
            if player == last_player:
                #delta_vector.append(1 / (date - last_date + games + last_games))
                delta_vector.append(1)
            else:
                delta_vector.append(0)
            last_player, last_date, last_games = player, date, games

        return self.time_delta * np.array(delta_vector)

    def create_vars(self, ratings, fparam):
        v = [0] * self.nrating_vars_
        for player, r in ratings.items():
            for date, rating in r.items():
                i = self.var_player_date_.index((player, date))
                v[i] = rating / 1000 - 1
        v += fparam
        return np.array(v, dtype=np.float64)

    def calc_smoothness_(self, rating_vars):
        rating_delta = (rating_vars[1:] - rating_vars[:-1])**2
        return np.inner(rating_delta, self.time_delta_vector_)

    def rating_delta_(self, v, index):
        if len(index):
            return v[index[:,0]] - v[index[:,1]]
        else:
            return np.array([])

    def objective(self, v, verbose=False):
        self.objective_calls += 1

        rating_vars = v[:self.nrating_vars_]
        self.f.reset_from_vars(v[self.nrating_vars_:])

        rating_diff = (rating_vars[self.games_player1_var_] -
                       rating_vars[self.games_player2_var_])

        likelihood = (self.f.sum_log(rating_diff[self.wins_slice_]) +
                      self.f.sum_log1m(rating_diff[self.losses_slice_]) +
                      self.f.sum_log(rating_diff[self.draws_slice_]) / 2 +
                      self.f.sum_log1m(rating_diff[self.draws_slice_]) / 2)

        regularization = np.linalg.norm(rating_vars) ** 2 * self.rating_reg

        smoothness = self.calc_smoothness_(rating_vars)

        f_hard_reg = self.f.hard_reg() * len(self.games_) * self.func_hard_reg
        f_soft_reg = self.f.soft_reg() * len(self.games_) * self.func_soft_reg

        total = (-likelihood + regularization + smoothness +
                  f_hard_reg + f_soft_reg)

        if verbose:
            return (total, likelihood, regularization, smoothness,
                    f_hard_reg, f_soft_reg)
        else:
            return total

    def likelihood_grad_(self, rating_diff):
        # d likelihood / d f(x)
        d = np.zeros(len(rating_diff))

        fdiffs = self.f.calc_vector(rating_diff)
        fdiffs[fdiffs < 1E-10] = 1E-10
        fdiffs[fdiffs > 1 - 1E-10] = 1 - 1E-10

        d[self.wins_slice_] = 1 / fdiffs[self.wins_slice_]
        d[self.losses_slice_] = -1 / (1 - fdiffs[self.losses_slice_])
        d[self.draws_slice_] = 0.5 * (
            1 / fdiffs[self.draws_slice_] - 1 / (1 - fdiffs[self.draws_slice_]))

        return d

    def grad_by_game_(self, rating_diff, d, l):
        g = np.zeros(l, dtype=np.float64)
        t = self.f.deriv(rating_diff) * d

        res = self.grad_by_game_m_ * t
        res = np.reshape(res, self.nrating_vars_)
        g[:self.nrating_vars_] = res

        return g

    def gradient(self, v):
        self.gradient_calls += 1
        self.f.reset_from_vars(v[self.nrating_vars_:])

        rating_vars = v[:self.nrating_vars_]
        rating_diff = (rating_vars[self.games_player1_var_] -
                       rating_vars[self.games_player2_var_])

        d = self.likelihood_grad_(rating_diff)
        g = self.grad_by_game_(rating_diff, d, len(v))

        g[self.nrating_vars_:] = np.dot(
            d, np.transpose(self.f.params_grad_vector(rating_diff)))

        g[:self.nrating_vars_] -= 2 * self.rating_reg * rating_vars

        vdelta_sign = np.sign(rating_vars[1:] - rating_vars[:-1])

        smoothness_grad = 2 * self.time_delta_vector_ * (rating_vars[1:] -
                                                         rating_vars[:-1])
        g[:self.nrating_vars_ - 1] += smoothness_grad
        g[1:self.nrating_vars_] -= smoothness_grad

        g[self.nrating_vars_:] -= (self.f.hard_reg_grad() * self.func_hard_reg *
                            len(self.games_))
        g[self.nrating_vars_:] -= (self.f.soft_reg_grad() * self.func_soft_reg *
                            len(self.games_))

        return -g


    def init(self):
        return np.array([random() - 0.5 for i in range(self.nrating_vars_)] +
                           self.f.init())

    def ratings_from_point(self, point):
        """Convert a point to player's ratings:

        Returns:
            {playerid: {date: rating}}
        """
        rating = {}
        for i in range(self.nrating_vars_):
            player, date = self.var_player_date_[i]
            if player not in rating:
                rating[player] = {}
            rating[player][date] = point[i] * 1000 + 2000
        return rating

    def callback(self, xk):
        if not self.disp:
            return
        self.optimization_steps += 1

        if (time.time() - self.last_check > 10 and
            self.optimization_steps - self.last_step_check > 10 or
            self.optimization_steps - self.last_step_check > 1000):
            o = self.objective(xk)
            gn = np.linalg.norm(self.gradient(xk))

            print(('Step {}. Objective {}, calculated {} times.\n' +
                  'Gradient norm {}, calculated {} times.').format(
                      self.optimization_steps, o, self.objective_calls,
                      gn, self.gradient_calls))
            sys.stdout.flush()

            self.last_step_check = self.optimization_steps
            self.last_check = time.time()


    def run(self, method='l-bfgs-b', maxiter=0):
        init_point = self.init()
        self.objective_calls = 0
        self.gradient_calls = 0
        self.optimization_steps = 0
        self.start_time = time.time()
        self.last_check = self.start_time
        self.last_step_check = 0
        grad = (self.gradient if method.lower() in ('cg', 'newton-cg', 'bfgs', 'l-bfgs-b')
                else None)
        options = {'disp': self.disp}
        if maxiter:
            options['maxiter'] = maxiter
        res = minimize(self.objective, init_point,
                       method=method,
                       options=options,
                       jac=grad,
                       callback=self.callback)
        ratings = self.ratings_from_point(res.x)
        self.f.reset_from_vars(res.x[self.nrating_vars_:])
        return ratings, self.f, res.x

    def random_solution(self):
        point = self.init()
        ratings = self.ratings_from_point(point)
        self.f.reset_from_vars(point[self.nrating_vars_:])
        return ratings, self.f
