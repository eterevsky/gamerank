import cProfile
import datetime
import pstats

from gamesdb import DataBase
from optimizer import Optimizer

def main(profile=False):
    db = DataBase('games.db')
    results = db.load_game_results(mingames=50)
    print('{} games loaded.'.format(len(results)))
    players = db.load_players()
    optimizer = Optimizer(disp=True)
    optimizer.load_games(results)
    maxiter = 30 if profile else 0
    ratings, f, v = optimizer.run(method='cg', maxiter=maxiter)

    if profile:
        return
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


def profiler():
    cProfile.run('main(True)')
    # cProfile.run('main(True)', 'opstats')
    # s = pstats.Stats('opstats')
    # s.print_callers()

if __name__ == '__main__':
    # profiler()
    main()
