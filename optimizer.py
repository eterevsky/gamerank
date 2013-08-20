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
    return 1 / cosh(x)

class WinningProbabilityFunction(object):
    """Probablity of winning based on difference of ratings.

    f(d) = P(A wins as white vs B as black | rating(A) - rating(B) = d)

    To normalize as in ELO rating, the following should hold:
    (f(200) + (1 - f(-200)) / 2 = 0.75,
    which is the same as:
    f(200) - f(-200) = 0.5

    The function is defined by its value in a set of points. The points are:
    -n*step, -(n-1)*step, ..., -2*step, -step, 0, step, 2*step, ..., n*step
    step should be chosen so that 200 = step*k for some integer k < n.

    f(-n*step) = 0
    f(n*step) = 1

    The values of the function in the points are extracted from 2*n parameters
    a[0] .. a[2*n - 1] in the following way:

    s = a[0] + ... + a[2*n - 1]
    f((i+1)*step) - f(i*step) = a[n + i] / s

    For x not in point:
    f(x) = 0 for x <= -n*step
    f(x) = 1 for x >= n* step
    f(x) = exp((log(k*step)*((k+1)*step - x) +
                log((k+1)*step) * (x - k*step))) / step)
             for k*step < x < (k+1)*step

    """

    def __init__(self, nparameters=8):
        assert nparameters % 2 == 0
        self.step = 100
        self.n = nparameters // 2
        self.max = self.n * self.step
        self.min = -self.max
        self.values_log = [0] * (2*self.n + 1)
        self.values_log[0] = -100
        self.s = 1

    def reset_from_vars(self, var):
        self.s = sum(var)
        v = 0
        for i in range(len(var)):
            v += var[i] / self.s
            if v > 0:
                self.values_log[i + 1] = log(v)
            else:
                self.values_log[i + 1] = -100
        assert abs(self.values_log[-1]) < 10**(-6)

    def calc(self, x):
        if x <= self.min:
            return 1E-10
        if x >= self.max:
            return 1.0 - 1E-10
        lo = -self.n
        hi = self.n
        while hi - lo > 1:
            mid = (hi + lo) // 2
            if x > mid * self.step:
                lo = mid
            else:
                hi = mid
        lx = self.step * lo
        hx = self.step * hi
        lf = self.values_log[lo + self.n]
        hf = self.values_log[hi + self.n]
        return exp((lf * (hx - x) + hf * (x - lx)) / self.step)

    def calc_vector(self, vx):
        return list(map(self.calc, vx))

    def hard_regularization(self):
        elo_norm = self.calc(200) - self.calc(-200)
        return (self.s - 1)**2 + (elo_norm - 0.5)**2

    def soft_regularization(self):
        s = 0
        x = self.min
        while x <= -400:
            s += self.calc(x) ** 2
            x += self.step
        while x <= 400:
            s += (self.calc(x) - (x + 400) / 800) ** 2
            x += self.step
        while x <= self.max:
            s += (self.calc(x) - 1) ** 2
            x += self.step
        return s

    def init(self):
        return [random() for i in range(2 * self.n)]


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
        return (1 + tanh((x - self.mu) / self.s)) / 2

    def deriv(self, x):
        return sech((x - self.mu) / self.s) ** 2 / (2 * self.s)

    def calc_vector(self, vx):
        return list(map(self.calc, vx))

    def calc_log(self, x):
        y = 2 * (x - self.mu) / self.s
        if y > 0:
            return -log(1 + exp(-y))
        else:
            return y - log(exp(y) + 1)

    def calc_log_vector(self, vx):
        return map(self.calc_log, vx)

    def sum_log_vector(self, vx):
        vy = 2 * (vx - self.mu) / self.s
        return (np.sum(-np.log(1 + np.exp(-vy[vy > 0]))) +
                np.sum(vy[vy <= 0] - np.log(np.exp(vy[vy <= 0]) + 1)))

    def sum_log_vector2(self, vx):
        return sum(self.calc_log_vector(vx))

    def calc_1mlog(self, x):
        """Calculate log(1 - f(x))"""
        y = 2 * (x - self.mu) / self.s
        if y > 0:
            return -y - log(1 + exp(-y))
        else:
            return -log(1 + exp(y))

    def calc_1mlog_vector(self, vx):
        return map(self.calc_1mlog, vx)

    def sum_1mlog_vector(self, vx):
        vy = 2 * (vx - self.mu) / self.s
        return (np.sum(-vy[vy > 0] - np.log(1 + np.exp(-vy[vy > 0]))) +
                np.sum(-np.log(1 + np.exp(vy[vy <= 0]))))

    def sum_1mlog_vector2(self, vx):
        return sum(self.calc_1mlog_vector(vx))

    def hard_regularization(self):
        elo_norm = self.calc(200) - self.calc(-200)
        return 1000 * (elo_norm - 0.5)**2

    def hard_reg_grad(self):
        arg1 = (200 - self.mu) / self.s
        arg2 = (-200 - self.mu) / self.s
        return (500 * (tanh(arg1) - tanh(arg2) - 1) *
                (sech(arg1)**2 * np.array([-1/self.s, -arg1/self.s]) -
                 sech(arg2)**2 * np.array([-1/self.s, -arg2/self.s])))

    def soft_regularization(self):
        return self.mu*self.mu + self.s*self.s / 10000

    def soft_reg_grad(self):
        return np.array([2 * self.mu, self.s / 5000 ])

    def params_grad(self, x):
        d = sech((x - self.mu) / self.s) ** 2
        return d * np.array([-1 / (2 * self.s),
                             (self.mu - x) / (2 * self.s * self.s)])


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
        self.games_ = results
        # player -> date -> games list
        self.player_date_games_ = self.generate_player_date_games_()
        self.rating_vars_index_, index_by_player_date = self.generate_rating_vars_index_()
        self.nvars_ = len(self.rating_vars_index_)
        self.time_delta_vector_ = self.generate_rating_deltas_()
        self.wins_rating_index_ = []
        self.losses_rating_index_ = []
        self.draws_rating_index_ = []
        for player1, player2, date, result in self.games_:
            indices = (index_by_player_date[(player1, date)],
                       index_by_player_date[(player2, date)])
            if result == 0:
                self.losses_rating_index_.append(indices)
            elif result == 1:
                self.wins_rating_index_.append(indices)
            else:
                self.draws_rating_index_.append(indices)
        self.wins_rating_index_ = np.array(self.wins_rating_index_)
        self.losses_rating_index_ = np.array(self.losses_rating_index_)
        self.draws_rating_index_ = np.array(self.draws_rating_index_)

        self.reg_mean_ = np.ones(self.nvars_, dtype=np.float64) * 2000.0

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

    def generate_rating_vars_index_(self):
        v = []
        index_by_player_date = {}
        for player in self.player_date_games_.keys():
            for date in sorted(self.player_date_games_[player].keys()):
                v.append((player, date))
                index_by_player_date[(player, date)] = len(v) - 1
        return v, index_by_player_date

    def generate_rating_deltas_(self):
        """Generate a table of coefficients to rating changes.

        1 / (difference in days for subsequent ratings) +
        1 / (the number of games between)

        TODO: Tune coefficients of each part.
        """

        delta_vector = []
        last_player, last_date = self.rating_vars_index_[0]
        last_games = self.player_date_games_[last_player][last_date]
        for player, date in self.rating_vars_index_[1:]:
            games = self.player_date_games_[player][date]
            if player == last_player:
                delta_vector.append(1 / (date - last_date + games + last_games))
            else:
                delta_vector.append(0)
            last_player, last_date, last_games = player, date, games

        return self.time_delta * np.array(delta_vector)

    def calc_deltas_(self, v):
        rating_delta = abs(v[1:self.nvars_] - v[0:self.nvars_ - 1])
        time_games_change = np.inner(rating_delta,
                                     self.time_delta_vector_)
        return time_games_change

    def create_vars(self, ratings, fparam):
        v = [0] * self.nvars_
        for player, r in ratings.items():
            for date, rating in r.items():
                i = self.rating_vars_index_.index((player, date))
                v[i] = rating
        v += fparam
        return np.array(v, dtype=np.float64)

    def rating_delta_(self, v, index):
        if len(index):
            return v[index[:,0]] - v[index[:,1]]
        else:
            return np.array([])

    def objective(self, v, verbose=False):
        self.objective_calls += 1

        self.f.reset_from_vars(v[self.nvars_:])

        wins_rating_delta = self.rating_delta_(v, self.wins_rating_index_)
        wins_likelihood = self.f.sum_log_vector(wins_rating_delta)

        losses_rating_delta = self.rating_delta_(v, self.losses_rating_index_)
        losses_likelihood = self.f.sum_1mlog_vector(losses_rating_delta)

        draws_rating_delta = self.rating_delta_(v, self.draws_rating_index_)
        draws_likelihood = (self.f.sum_log_vector(draws_rating_delta) +
                            self.f.sum_1mlog_vector(draws_rating_delta)) / 2

        regularization = np.linalg.norm(v[:self.nvars_] - self.reg_mean_) ** 2

        time_games_change = self.calc_deltas_(v)

        func_hard_reg = self.f.hard_regularization()
        func_soft_reg = self.f.soft_regularization()

        total = (wins_likelihood + losses_likelihood + draws_likelihood -
            self.rating_reg * regularization -
            time_games_change -
            self.func_hard_reg * func_hard_reg * len(self.games_) -
            self.func_soft_reg * func_soft_reg * len(self.games_))

        if verbose:
            return (-total, wins_likelihood, losses_likelihood,
                    draws_likelihood, self.rating_reg * regularization,
                    time_games_change, func_hard_reg, func_soft_reg)
        else:
            return -total

    def gradient(self, v):
        self.gradient_calls += 1
        self.f.reset_from_vars(v[self.nvars_:])
        g = np.zeros(len(v), dtype=np.float64)

        for a, b in self.wins_rating_index_:
            rating_diff = v[a] - v[b]
            d = 1 / self.f.calc(rating_diff)
            t = self.f.deriv(rating_diff) * d
            g[a] += t
            g[b] -= t
            g[self.nvars_:] += self.f.params_grad(rating_diff) * d

        for a, b in self.losses_rating_index_:
            rating_diff = v[a] - v[b]
            d = - 1 / (1 - self.f.calc(rating_diff))
            t = self.f.deriv(rating_diff) * d
            g[a] += t
            g[b] -= t
            g[self.nvars_:] += self.f.params_grad(rating_diff) * d

        for a, b in self.draws_rating_index_:
            rating_diff = v[a] - v[b]
            d = (1 / self.f.calc(rating_diff) -
                 1 / (1 - self.f.calc(rating_diff))) / 2
            t = self.f.deriv(rating_diff) * d
            g[a] += t
            g[b] -= t
            g[self.nvars_:] += self.f.params_grad(rating_diff) * d

        g[:self.nvars_] -= 2 * self.rating_reg * (v[:self.nvars_] - self.reg_mean_)

        vdelta_sign = np.sign(v[1:self.nvars_] - v[:self.nvars_ - 1])
        g[:self.nvars_ - 1] += self.time_delta_vector_ * vdelta_sign
        g[1:self.nvars_] -= self.time_delta_vector_ * vdelta_sign

        g[self.nvars_:] -= (self.f.hard_reg_grad() * self.func_hard_reg *
                            len(self.games_))
        g[self.nvars_:] -= (self.f.soft_reg_grad() * self.func_soft_reg *
                            len(self.games_))

        return -g


    def init(self):
        return np.array([2000 + 1000*random() for i in range(self.nvars_)] +
                           self.f.init())

    def ratings_from_point(self, point):
        """Convert a point to player's ratings:

        Returns:
            {playerid: {date: rating}}
        """
        rating = {}
        for i in range(self.nvars_):
            player, date = self.rating_vars_index_[i]
            if player not in rating:
                rating[player] = {}
            rating[player][date] = point[i]
        return rating

    def callback(self, xk):
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
        self.f.reset_from_vars(res.x[self.nvars_:])
        return ratings, self.f, res.x

    def random_solution(self):
        point = self.init()
        ratings = self.ratings_from_point(point)
        self.f.reset_from_vars(point[self.nvars_:])
        return ratings, self.f
