import datetime

from gamesdb import DataBase
from optimizer import Optimizer

def main():
    db = DataBase('games.db')
    results = db.load_game_results()
    print('{} games loaded.'.format(len(results)))
    players = db.load_players()
    optimizer = Optimizer(disp=True)
    optimizer.load_games(results)
    ratings, f, v = optimizer.run(method='cg')

    print()
    print(optimizer.objective(v, verbose=True))
    print()

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
    print(f.calc(0.2) - f.calc(-0.2))
    print(list(sorted(by_rating))[-10:])


if __name__ == '__main__':
    main()
