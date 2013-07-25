import unittest

from game import PGNParser, Game
from gamesdb import DataBase


class TestGamesDB(unittest.TestCase):

    def test_player(self):
        db = DataBase(path=':memory:')
        db.create_schema('games.sql')

        id1 = db.get_player('Pupkin, Vasily')
        self.assertEqual(db.get_player('Pupkin, Vasily'), id1)
        id2 = db.get_player('Syutkin, Vladimir')
        self.assertNotEqual(id1, id2)
        self.assertEqual(db.get_player('Syutkin, Vladimir'), id2)
        self.assertEqual(db.get_player('Pupkin, Vasily'), id1)

    def test_add_game(self):
        db = DataBase(path=':memory:')
        db.create_schema('games.sql')

        game1 = Game(result=1,
                     player1_name='Pupkin, Vasily',
                     player2_name='Syutkin, Vladimir',
                     date='2010-09-30',
                     moves=['e4', 'e5', 'Nf3', 'Nc6', 'Bb5', 'a6', 'Ba4',
                            'Nf6', 'O-O', 'Be7', 'Re1', 'b5', 'Bb3', 'd6',
                            'c3', 'O-O', 'h3', 'Nb8', 'd4', 'Nbd7'],
                     tags={'Round': '13', 'Event': 'Abc'})

        id1 = db.add_game(game1)
        self.assertEqual(id1, game1.gameid)
        self.assertIsNotNone(id1)

        game1_test = db.load_game(id1)
        self.assertEqual(game1_test.gameid, id1)
        self.assertEqual(game1_test.moves, game1.moves)
        self.assertEqual(game1_test.result, 1)
        self.assertEqual(game1_test.player1_name, 'Pupkin, Vasily')
        self.assertEqual(game1_test.player2_name, 'Syutkin, Vladimir')
        self.assertIsNotNone(game1.player1_id)
        self.assertIsNotNone(game1.player2_id)
        self.assertEqual(game1_test.player1_id, game1.player1_id)
        self.assertEqual(game1_test.player2_id, game1.player2_id)
        self.assertNotEqual(game1.player1_id, game1.player2_id)
        self.assertEqual(game1_test.date_str(), '2010-09-30')



if __name__ == '__main__':
    unittest.main()

