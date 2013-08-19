import datetime

from gamesdb import DataBase
from optimizer import Optimizer

def main():
    db = DataBase('games.db')
    results = db.load_game_results(mingames=100)
    players = db.load_players()
    optimizer = Optimizer(disp=True, rating_reg=1E-6, time_delta=1E-2)
    optimizer.load_games(results)
    ratings, f, _ = optimizer.run()
    by_rating = []
    for iplayer, rating in ratings.items():
        print(players[iplayer])
        mr = 0
        for date, r in sorted(rating.items()):
            date = datetime.date.fromtimestamp(date * 24 * 3600)
            print(date.isoformat(), r)
            if r > mr:
                mr = r
        by_rating.append((mr, players[iplayer]))

        print()
    print(f)
    print(f.calc(200) - f.calc(-200))
    print(list(sorted(by_rating))[-10:])


if __name__ == '__main__':
    main()
