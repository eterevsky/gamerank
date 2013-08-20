from math import cosh, exp, log, tanh
import numpy as np
from random import random, seed
import time

try:
  from scipy.optimize import minimize
except ImportError:
  from scipy.optimize import fmin, fmin_powell, fmin_cg, fmin_bfgs, fmin_ncg

  def minimize(func, x0, method='CG', options=None, jac=None, callback=None):
      method = method.lower()

      if 'disp' in options:
          disp=options['disp']

      if method == 'nelder-mead':
          x = fmin(func=func, x0=x0, disp=disp, callback=callback)
      elif method == 'powell':
          x =  fmin_powell(func=func, x0=x0, disp=disp, callback=callback)
      elif method == 'cg':
          x = fmin_cg(f=func, x0=x0, fprime=jac, disp=disp, callback=callback)
      elif method == 'bfgs':
          x = fmin_bfgs(f=func, x0=x0, fprime=jac, disp=disp, callback=callback)
      elif method == 'newton-cg':
          x = fmin_ncg(f=func, x0=x0, fprime=jac, disp=disp, callback=callback)

      class Result(object):
          def __init__(self, x):
              self.x = x

      return Result(x)


def sech(x):
    return 1 / np.cosh(x)


class LogisticProbabilityFunction(object):
    def __init__(self):
        self.mu = 0
        self.s = 1

    def init(self):
        return [0, 400]

    def reset_from_vars(self, var):
        self.mu, self.s = var[0], var[1]

    def __str__(self):
        return "(1 + tanh((x - {}) / {})) / 2".format(self.mu, self.s)

    def calc(self, x):
        return 0.5 + 0.5 * tanh((x - self.mu) / self.s)

    def calc_vector(self, x):
        return 0.5 + 0.5 * np.tanh((x - self.mu) / self.s)

    def deriv(self, x):
        return sech((x - self.mu) / self.s) ** 2 / (2 * self.s)

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
        return (np.sum(-np.log(1 + np.exp(-vy[vy > 0]))) +
                np.sum(vy[vy <= 0] - np.log(np.exp(vy[vy <= 0]) + 1)))

    def sum_log2(self, vx):
        return sum(self.calc_log_vector(vx))

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
        return (np.sum(-vy[vy > 0] - np.log(1 + np.exp(-vy[vy > 0]))) +
                np.sum(-np.log(1 + np.exp(vy[vy <= 0]))))

    def sum_log1m2(self, vx):
        return sum(self.calc_log1m_vector(vx))

    def hard_reg(self):
        elo_norm = self.calc(200) - self.calc(-200)
        return 1000 * (elo_norm - 0.5)**2

    def hard_reg_grad(self):
        arg1 = (200 - self.mu) / self.s
        arg2 = (-200 - self.mu) / self.s
        return (500 * (tanh(arg1) - tanh(arg2) - 1) *
                (sech(arg1)**2 * np.array([-1/self.s, -arg1/self.s]) -
                 sech(arg2)**2 * np.array([-1/self.s, -arg2/self.s])))

    def soft_reg(self):
        return self.mu*self.mu + self.s*self.s / 10000

    def soft_reg_grad(self):
        return np.array([2 * self.mu, self.s / 5000 ])

    def params_grad(self, x):
        d = sech((x - self.mu) / self.s) ** 2
        return d * np.array([-1 / (2 * self.s),
                            (self.mu - x) / (2 * self.s * self.s)])

    def params_grad_vector(self, x):
        d = sech((x - self.mu) / self.s) ** 2
        return np.array([-d / (2 * self.s),
                         d * (self.mu - x) / (2 * self.s * self.s)])


class Optimizer(object):
    def __init__(self, disp=False, func_hard_reg=100.0, func_soft_reg=0.01,
                 time_delta=0.2, rating_reg=1E-4, rand_seed=None):
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

        self.games_player1_var_ = []
        self.games_player2_var_ = []
        for player1, player2, date, _ in self.games_:
            self.games_player1_var_.append(player_date_var[(player1, date)])
            self.games_player2_var_.append(player_date_var[(player2, date)])

        self.games_player1_var_ = np.array(self.games_player1_var_)
        self.games_player2_var_ = np.array(self.games_player2_var_)

        self.reg_mean_ = np.ones(self.nrating_vars_, dtype=np.float64) * 2000.0

    def create_game_result_slices_(self, games):
        last_loss = -1
        last_win = -1
        for i in range(len(games)):
            if games[i][3] == '0':
                last_loss = i
                last_win = i
            elif games[i][3] == '1':
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
                delta_vector.append(1 / (date - last_date + games + last_games))
            else:
                delta_vector.append(0)
            last_player, last_date, last_games = player, date, games

        return self.time_delta * np.array(delta_vector)

    def create_vars(self, ratings, fparam):
        v = [0] * self.nrating_vars_
        for player, r in ratings.items():
            for date, rating in r.items():
                i = self.var_player_date_.index((player, date))
                v[i] = rating
        v += fparam
        return np.array(v, dtype=np.float64)

    def calc_smoothness_(self, rating_vars):
        rating_delta = abs(rating_vars[1:] - rating_vars[:-1])
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

        regularization = (np.linalg.norm(rating_vars - self.reg_mean_) ** 2 *
                          self.rating_reg)

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

    def gradient(self, v):
        self.gradient_calls += 1
        self.f.reset_from_vars(v[self.nrating_vars_:])
        g = np.zeros(len(v), dtype=np.float64)

        rating_vars = v[:self.nrating_vars_]
        self.f.reset_from_vars(v[self.nrating_vars_:])

        rating_diff = (rating_vars[self.games_player1_var_] -
                       rating_vars[self.games_player2_var_])

        # d likelihood / d f(x)
        d = np.zeros(len(rating_diff))
        d[self.wins_slice_] = 1 / self.f.calc_vector(rating_diff[self.wins_slice_])
        d[self.losses_slice_] = -1 / (1 - self.f.calc_vector(rating_diff[self.losses_slice_]))
        d[self.draws_slice_] = (
            1 / self.f.calc_vector(rating_diff[self.draws_slice_]) -
            1 / (1 - self.f.calc_vector(rating_diff[self.draws_slice_])))

        t = self.f.deriv(rating_diff) * d

        for i in range(len(t)):
            g[self.games_player1_var_[i]] += t[i]
            g[self.games_player2_var_[i]] -= t[i]

        g[self.nrating_vars_:] = np.dot(
            d, np.transpose(self.f.params_grad_vector(rating_diff)))

        g[:self.nrating_vars_] -= 2 * self.rating_reg * (rating_vars - self.reg_mean_)

        vdelta_sign = np.sign(rating_vars[1:] - rating_vars[:-1])
        g[:self.nrating_vars_ - 1] += self.time_delta_vector_ * vdelta_sign
        g[1:self.nrating_vars_] -= self.time_delta_vector_ * vdelta_sign

        g[self.nrating_vars_:] -= (self.f.hard_reg_grad() * self.func_hard_reg *
                            len(self.games_))
        g[self.nrating_vars_:] -= (self.f.soft_reg_grad() * self.func_soft_reg *
                            len(self.games_))

        return -g


    def init(self):
        return np.array([2000 + 1000*random() for i in range(self.nrating_vars_)] +
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
            rating[player][date] = point[i]
        return rating

    def callback(self, xk):
        if not self.disp:
            return
        self.optimization_steps += 1

        if (time.time() - self.last_check > 10 or
            self.optimization_steps - self.last_step_check > 1000):
            o = self.objective(xk)
            gn = np.linalg.norm(self.gradient(xk))

            print(('Step {}. Objective {}, calculated {} times.\n' +
                  'Gradient norm {}, calculated {} times.').format(
                      self.optimization_steps, o, self.objective_calls,
                      gn, self.gradient_calls))

            self.last_step_check = self.optimization_steps
            self.last_check = time.time()


    def run(self, method='cg'):
        init_point = self.init()
        self.objective_calls = 0
        self.gradient_calls = 0
        self.optimization_steps = 0
        self.start_time = time.time()
        self.last_check = self.start_time
        self.last_step_check = 0
        res = minimize(self.objective, init_point,
                       method=method,
                       options={'disp': self.disp},
                       jac=self.gradient,
                       callback=self.callback)
        ratings = self.ratings_from_point(res.x)
        self.f.reset_from_vars(res.x[self.nrating_vars_:])
        return ratings, self.f, res.x

    def random_solution(self):
        point = self.init()
        ratings = self.ratings_from_point(point)
        self.f.reset_from_vars(point[self.nrating_vars_:])
        return ratings, self.f
