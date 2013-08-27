import argparse
import cProfile
import datetime
import pstats

from gamesdb import DataBase
from optimizer import Optimizer

def main(args, profile=False):
    db = DataBase(args.games)
    results = db.load_game_results(mingames=50)
    print('{} games loaded.'.format(len(results)))
    players = db.load_players()
    optimizer = Optimizer(disp=True)
    optimizer.load_games(results)
    maxiter = 30 if profile else 0
    ratings, f, v = optimizer.run(method='l-bfgs-b', maxiter=maxiter)

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

    best = list(sorted(by_rating))[-20:]
    for r, p in reversed(best):
        print('{:24} {}'.format(p, r))


def profiler(args):
    cProfile.runctx('main(args, profile=True)', {'args': args})
    # cProfile.run('main(True)', 'opstats')
    # s = pstats.Stats('opstats')
    # s.print_callers()

def parse_command_line():
    parser = argparse.ArgumentParser(description='Optimize ratings.')

    parser.add_argument('-p', '--profile', action='store_true')
    parser.add_argument('-g', '--games', default='games.db')

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_command_line()
    if args.profile:
        profiler(args)
    else:
        main(args)
