import datetime

from gamesdb import DataBase
from optimizer import Optimizer

def main():
    db = DataBase('games.db')
    results = db.load_game_results()
    players = db.load_players()
    optimizer = Optimizer(disp=True, rating_reg=1E-4, time_delta=1E-3, games_delta=1E-3)
    optimizer.load_games(results)
    ratings, _, _ = optimizer.run()
    for iplayer, rating in ratings.items():
        print(players[iplayer])
        for date, r in sorted(rating.items()):
            date = datetime.date.fromtimestamp(date * 24 * 3600)
            print(date.isoformat(), r)
        print()

if __name__ == '__main__':
    main()
