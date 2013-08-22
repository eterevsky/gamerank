import datetime
import math
import os.path
import sqlite3

from game import Game, lastname_from_name

YEAR = 365 * 24 * 3600


def _dates_compatible(date1, date1_precision, date2, date2_precision):
    d1 = datetime.date.fromtimestamp(date1)
    d2 = datetime.date.fromtimestamp(date2)

    precision = max(date1_precision, date2_precision)

    if precision < 3 and d1.year != d2.year:
        return False

    if precision < 2 and d1.month != d2.month:
        return False

    if precision == 0 and d1.day != d2.day:
        return False

    return True


class DuplicateGameError(Exception):
    pass


class DataBase(object):

    def __init__(self, path='games.db'):
        self._conn = sqlite3.connect(path)
        if self._unintialized():
            self.create_schema(path='games.sql')

    def _unintialized(self):
        try:
            self._conn.execute('SELECT count(*) FROM game')
        except sqlite3.OperationalError:
            return True
        return False

    def create_schema(self, path):
        with open(path) as schema_file:
            self._conn.executescript(schema_file.read())

    def load_game(self, gameid):
        cursor = self._conn.cursor()
        cursor.execute("""SELECT result, date, dateprecision, moves,
                                 playerid1, player1.name,
                                 playerid2, player2.name
                          FROM game, player as player1, player as player2
                          WHERE gameid=?
                            AND playerid1=player1.playerid
                            AND playerid2=player2.playerid""", (gameid,))
        row = cursor.fetchone()
        if not row:
            return None
        game = Game(gameid=gameid,
                    result=row[0],
                    date=row[1],
                    date_precision=row[2],
                    moves=list(row[3].split()),
                    player1_id=row[4],
                    player1_name=row[5],
                    player2_id=row[6],
                    player2_name=row[7])
        cursor.execute('SELECT name, value FROM tag WHERE gameid=?',
                       (gameid,))
        for row in cursor.fetchall():
            game.add_tag(row[0], row[1])

        return game

    def load_players(self):
        cursor = self._conn.cursor()
        cursor.execute('SELECT playerid, name FROM player')
        players = {}
        for row in cursor:
            players[row[0]] = row[1]
        return players

    def load_game_results_mingames(self, mingames=1):
        cursor = self._conn.cursor()

        cursor.execute("""SELECT playerid
                            FROM (SELECT player.playerid, count(*) AS c
                                  FROM player, game
                                  WHERE player.playerid=game.playerid1
                                     OR player.playerid=game.playerid2
                                  GROUP BY player.playerid)
                           WHERE c > ?""",
                       (mingames,))

        players = list(x[0] for x in cursor)

        cursor.execute("""SELECT playerid1, playerid2, date / (24*3600), result
                          FROM game
                          WHERE dateprecision=0
                            AND playerid1 IN ({p})
                            AND playerid2 IN ({p})""".format(
                                p=(', '.join(map(str, players)))))
        results = []
        for row in cursor:
            results.append(tuple(row))
        return results

    def load_game_results(self, mingames=1):
        if mingames > 1:
            return self.load_game_results_mingames(mingames)

        cursor = self._conn.cursor()

        cursor.execute("""SELECT playerid1, playerid2, date / (24*3600), result
                          FROM game
                          WHERE dateprecision=0""")
        results = []
        for row in cursor:
            results.append(tuple(row))
        return results

    def find_game(self, game):
        moves = game.moves_str()
        cursor = self._conn.cursor()
        cursor.execute("""SELECT gameid, result, date, dateprecision,
                                 player1.name, player2.name
                          FROM game, player as player1, player as player2
                          WHERE moves=?
                            AND playerid1=player1.playerid
                            AND playerid2=player2.playerid""",
                       (moves,))
        for row in cursor.fetchall():
            if (row[1] == game.result and
                _dates_compatible(game.date, game.date_precision,
                                  row[2], row[3]) and
                lastname_from_name(row[4]) == game.player1_lastname() and
                lastname_from_name(row[5]) == game.player2_lastname()):
                return row[0]
            elif len(game.moves) >= 19:
                raise DuplicateGameError(
                    'Two games with the same moves, but ' +
                    'different metadata:\n' +
                    'DB: ' + str(self.load_game(row[0])) + '\n' +
                    'New: ' + str(game))

    def get_player(self, name):
        cursor = self._conn.cursor()
        cursor.execute('SELECT playerid FROM player WHERE name=?', (name,))
        row = cursor.fetchone()
        if row:
            return row[0]
        cursor.execute('INSERT INTO player(name) VALUES (?)', (name,))
        cursor.execute("""SELECT playerid FROM player
                          WHERE rowid=last_insert_rowid()""")
        return cursor.fetchone()[0]

    def add_game(self, game):
        gameid = self.find_game(game)
        if gameid:
            game.gameid = gameid
            return gameid

        if not game.player1_id:
            game.player1_id = self.get_player(game.player1_name)
        if not game.player2_id:
            game.player2_id = self.get_player(game.player2_name)

        cursor = self._conn.cursor()

        cursor.execute("""INSERT INTO game(playerid1, playerid2, result, date,
                                           dateprecision, moves)
                          VALUES (?, ?, ?, ?, ?, ?)""",
                       (game.player1_id, game.player2_id, game.result,
                        game.date, game.date_precision, game.moves_str()))

        cursor.execute("""SELECT gameid FROM game
                          WHERE rowid=last_insert_rowid()""")
        game.gameid = cursor.fetchone()[0]

        for name, value in game.tags.items():
            cursor.execute("""INSERT INTO tag(gameid, name, value)
                              VALUES (?, ?, ?)""",
                           (game.gameid, name, value))

        return game.gameid

    def commit(self):
        self._conn.commit()
