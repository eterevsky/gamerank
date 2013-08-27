import sys

from game import PGNParser
from gamesdb import DataBase, DuplicateGameError

if len(sys.argv) < 2:
    print('Usage:\npython3 import_pgn.py <pgn files>')
    exit(0)

db = DataBase('games.db')

for filename in sys.argv[1:]:
    parser = PGNParser(open(filename, encoding='iso-8859-1'))
    errors = []
    for game in parser.parse():
        try:
            db.add_game(game)
        except DuplicateGameError as error:
            errors.append(error)
        print(game)
    db.commit()

if len(errors):
    print('Errors:')
    for e in errors:
        print(e)

