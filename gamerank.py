from gamesdb import DataBase


class Optimizer(object):
    def __init__(self, results):
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




def main():
    db = DataBase('games.db')
    results = db.load_game_results()
    optimizer = Optimizer(results)
    optimizer.run()
    optimizer.normalize_by_max(3000)
    results = optimizer.results()
    players = db.load_players()
    for iplayer, rating in results:
        print(players[iplayer], rating)

if __name__ == '__main__':
    main()