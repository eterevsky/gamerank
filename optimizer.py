import math

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
                self.values_log[i + 1] = math.log(v)
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
        return math.exp((lf * (hx - x) + hf * (x - lx)) / self.step)

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


class Optimizer(object):
    def __init__(self, f_points_max=2000, f_points_step=2):
        self.f_points_max_ = f_points_max
        self.f_points_step_ = f_points_step

    def load_results(results):
        self.games_ = results
        self.populate_players_and_dates_(results)

    def populate_players_and_dates_(self, results):
        # player -> date -> games list
        player_date_games = {}
        for player1, player2, date, _ in results:
            if player1 not in player_date_games:
                player_date_games[player1] = {}
            if date not in dates_by_players[player1]:
                dates_by_players[player1][date] = 0
            dates_by_players[player1][date] += 1

            if player2 not in dates_by_players:
                dates_by_players[player2] = {}
            if date not in dates_by_players[player2]:
                dates_by_players[player2][date] = 0
            dates_by_players[player2][date] += 1

        self.var_player_ = []
        self.var_date_ = []
        self.var_date_delta_ = []
        self.var_ngames_ = []
        # Number of games on the date i-1 and i.
        self.var_ngames_delta_ = []

        self.player_date_to_idx = {}

        for player in sorted(dates_by_players.keys()):
            for date in sorted(dates_by_players[player].keys()):
                ngames_on_date = dates_by_players[player][date]
                if len(self.var_player_) > 0:
                    if player == self.var_player_[-1]:
                        self.var_date_delta_.append(date - self.var_date_[-1])
                        self.var_ngames_delta_.append(ngames_on_date +
                                                      self.var_ngames_[-1])
                    else:
                        self.var_date_delta_.append(None)
                        self.var_ngames_delta_.append(None)
                self.player_date_to_idx[(player, date)] = len(self.var_player_)
                self.var_player_.append(player)
                self.var_date_.append(date)
                self.var_ngames_.append(ngames_on_date)

    def objective(self, v):
        rating_vars = v[:len(self.var_ngames_)]
        function_vars = v[len(self.var_ngames_):]

        f = self.construct_function(function_vars)
