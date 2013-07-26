import sys

from game import PGNParser
from gamesdb import DataBase

if len(sys.argv) != 2:
    print('Usage:\npython3 import_pgn.py <pgn file>')
    exit(0)

db = DataBase('games.db')
parser = PGNParser(open(sys.argv[1], encoding='iso-8859-1'))
for game in parser.parse():
    db.add_game(game)
    print(game)

