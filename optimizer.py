from math import exp, log
from random import random
from scipy.optimize import fmin_bfgs, fmin_ncg

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

    def __init__(self, n_points=20, steps_in_200=2):
        self.n = n_points
        self.step = 200 / steps_in_200
        self.max = self.n * self.step
        self.min = -self.max
        self.steps_in_200 = steps_in_200
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
            return 0.0
        if x >= self.max:
            return 1.0
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


class Optimizer(object):
    def __init__(self):
        self.f = WinningProbabilityFunction()
        self.ref_coef = 0.01
        self.func_reg_coef = 1.0
        self.func_soft_reg_coef = 0.1

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
        self.rating_delta_coefficients_ = self.generate_rating_deltas_()
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
                index_by_player_date[(player, date)] = len(v)
        return v, index_by_player_date

    def generate_rating_deltas_(self):
        """Generate a table of coefficients to rating changes.

        1 / (difference in days for subsequent ratings) +
        1 / (the number of games between)

        TODO: Tune coefficients of each part.
        """

        delta_coef = []
        last_player, last_date = self.rating_vars_index_[0]
        last_games = self.player_date_games_[last_player][last_date]
        for player, date in self.rating_vars_index_[1:]:
            games = self.player_date_games_[player][date]
            if player == last_player:
                delta_coef.append(1 / (date - last_date) +
                                  1 / (games + last_games))
            else:
                delta_coef.append(0)
            last_player, last_date, last_games = player, date, games

        return delta_coef

    def regularization(self, v):
        r = sum((vv - 2000)**2 for vv in v) / 10000
        for i in range(len(v) - 1):
            r += self.rating_delta_coefficients_[i] * abs(v[i + 1] - v[i])
        return r

    def objective(self, v):
        self.f.reset_from_vars(v[self.nvars_:])

        wins_rating_delta = ((v[i] - v[j]) for i, j in self.wins_rating_index_)
        wins_probabilities = self.f.calc_vector(wins_rating_delta)
        wins_likelihood = sum(log(p) for p in wins_probabilities)

        losses_rating_delta = (v[i] - v[j] for i, j in self.losses_rating_index_)
        losses_probabilities = self.f.calc_vector(losses_rating_delta)
        losses_likelihood = sum(log(1 - p) for p in losses_probabilities)

        draws_rating_delta = (v[i] - v[j] for i, j in self.draws_rating_index_)
        draws_probabilities = self.f.calc_vector(draws_rating_delta)
        draws_likelihood = sum(log(p) + log(1 - p)
                               for p in draws_probabilities) / 2

        return (wins_likelihood + losses_likelihood + draws_likelihood -
                self.regularization(v[:self.nvars_]) -
                self.func_reg_coef * self.f.hard_regularization() -
                self.func_soft_reg_coef * self.f.soft_regularization())

    def init(self):
        return [2000 + random() for i in range(self.nvars_)] + self.f.init()

    def run(self):
        init_point = self.init()
        def show(*args):
            print(args)
        res = fmin_bfgs(self.objective, init_point, disp=True, callback=show)
        self.f.reset_from_vars(res[self.nvars_:])
        for x in range(-400, 401, 50):
            print('f({}) = {}'.format(x, self.f.calc(x)))

