import unittest

from game import PGNParser, Game, _parse_date
from gamesdb import DataBase, _dates_compatible


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
        self.assertIsNotNone(game1.player1_id)
        self.assertIsNotNone(game1.player2_id)
        self.assertNotEqual(game1.player1_id, game1.player2_id)

        game1_test = db.load_game(id1)
        self.assertEqual(game1_test.gameid, id1)
        self.assertEqual(game1_test.moves, game1.moves)
        self.assertEqual(game1_test.result, 1)
        self.assertEqual(game1_test.player1_name, 'Pupkin, Vasily')
        self.assertEqual(game1_test.player2_name, 'Syutkin, Vladimir')
        self.assertEqual(game1_test.player1_id, game1.player1_id)
        self.assertEqual(game1_test.player2_id, game1.player2_id)
        self.assertEqual(game1_test.date_str(), '2010-09-30')
        self.assertEqual(game1_test.date_precision, 0)
        self.assertEqual(game1_test.tags['Round'], '13')
        self.assertEqual(game1_test.tags['Event'], 'Abc')

        game2 = Game(result=0,
                     player1_name='Syutkin, Vladimir',
                     player2_name='Assange, Julian',
                     date='2005-06-??',
                     moves=['e4', 'e5', 'Nf3', 'Nc6', 'Bb5', 'a6', 'Ba4',
                            'Nf6', 'O-O', 'Be7', 'Re1', 'b5', 'Bb3', 'd6',
                            'c3', 'O-O', 'h3', 'Nb8'],
                     tags={'Round': '13', 'Event': 'Abc'})

        id2 = db.add_game(game2)
        self.assertEqual(id2, game2.gameid)
        self.assertIsNotNone(id2)
        self.assertNotEqual(id2, id1)
        self.assertIsNotNone(game2.player2_id)
        self.assertEqual(game2.player1_id, game1.player2_id)

        game2_test = db.load_game(id2)
        self.assertEqual(game2_test.gameid, id2)
        self.assertEqual(game2_test.moves, game2.moves)
        self.assertEqual(game2_test.result, 0)
        self.assertEqual(game2_test.player1_name, 'Syutkin, Vladimir')
        self.assertEqual(game2_test.player2_name, 'Assange, Julian')
        self.assertEqual(game2_test.date_str(), '2005-06-??')
        self.assertEqual(game2_test.date_precision, 1)

    def test_find_game(self):
        db = DataBase(path=':memory:')
        db.create_schema('games.sql')

        game1 = Game(result=1,
                     player1_name='Pupkin, Vasily',
                     player2_name='Syutkin, Vladimir',
                     date='2010-09-??',
                     moves=['e4', 'e5', 'Nf3', 'Nc6', 'Bb5', 'a6', 'Ba4',
                            'Nf6', 'O-O', 'Be7', 'Re1', 'b5', 'Bb3', 'd6',
                            'c3', 'O-O', 'h3', 'Nb8', 'd4', 'Nbd7'],
                     tags={'Round': '13', 'Event': 'Abc'})
        id1 = db.add_game(game1)

        game2 = Game(result=0,
                     player1_name='Syutkin, Vladimir',
                     player2_name='Assange, Julian',
                     date='2005-06-??',
                     moves=['e4', 'e5', 'Nf3', 'Nc6', 'Bb5', 'a6', 'Ba4',
                            'Nf6', 'O-O', 'Be7', 'Re1', 'b5', 'Bb3', 'd6',
                            'c3', 'O-O', 'h3', 'Nb8'],
                     tags={'Round': '13', 'Event': 'Abc'})

        self.assertIsNone(db.find_game(game2))

        id2 = db.add_game(game2)

        game3 = Game(result=1,
                     player1_name='Pupkin, Vasily',
                     player2_name='Syutkin, Vladimir',
                     date='2010-??-??',
                     moves=['e4', 'e5', 'Nf3', 'Nc6', 'Bb5', 'a6', 'Ba4',
                            'Nf6', 'O-O', 'Be7', 'Re1', 'b5', 'Bb3', 'd6',
                            'c3', 'O-O', 'h3', 'Nb8', 'd4', 'Nbd7'],
                     tags={'Round': '14', 'Event': 'Cba'})

        self.assertEqual(db.find_game(game3), id1)
        self.assertEqual(db.add_game(game3), id1)
        self.assertEqual(game3.gameid, id1)

        game4 = Game(result=2,
                     player1_name='Pupkin, Vasily',
                     player2_name='Syutkin, Vladimir',
                     date='????-??-??',
                     moves=['e4', 'e5'])
        id4 = db.add_game(game4)

        game5 = Game(result=2,
                     player1_name='Assange, Julian',
                     player2_name='Syutkin, Vladimir',
                     date='1993-??-??',
                     moves=['e4', 'e5'])
        self.assertIsNone(db.find_game(game5))

        game6 = Game(result=1,
                     player1_name='Pupkin, Vasily',
                     player2_name='Syutkin, Vladimir',
                     date='2009-??-??',
                     moves=['e4', 'e5', 'Nf3', 'Nc6', 'Bb5', 'a6', 'Ba4',
                            'Nf6', 'O-O', 'Be7', 'Re1', 'b5', 'Bb3', 'd6',
                            'c3', 'O-O', 'h3', 'Nb8', 'd4', 'Nbd7'],
                     tags={'Round': '13', 'Event': 'Abc'})
        with self.assertRaises(Exception):
            db.find_game(game6)

    def test_dates_compatible(self):
        date1, precision1 = _parse_date('????-??-??')
        self.assertTrue(_dates_compatible(date1, precision1, date1, precision1))
        date2, precision2 = _parse_date('2005-??-??')
        self.assertTrue(_dates_compatible(date1, precision1, date2, precision2))
        date3, precision3 = _parse_date('2006-??-??')
        self.assertFalse(_dates_compatible(date3, precision3, date2, precision2))
        date4, precision4 = _parse_date('2005-12-??')
        self.assertTrue(_dates_compatible(date1, precision1, date4, precision4))
        self.assertTrue(_dates_compatible(date2, precision2, date4, precision4))
        self.assertFalse(_dates_compatible(date3, precision3, date4, precision4))
        date5, precision5 = _parse_date('2005-10-??')
        self.assertFalse(_dates_compatible(date4, precision4, date5, precision5))
        date6, precision6 = _parse_date('2006-10-??')
        self.assertTrue(_dates_compatible(date3, precision3, date6, precision6))
        self.assertFalse(_dates_compatible(date5, precision5, date6, precision6))
        date7, precision7 = _parse_date('2005-10-05')
        self.assertTrue(_dates_compatible(date1, precision1, date7, precision7))
        self.assertTrue(_dates_compatible(date2, precision2, date7, precision7))
        self.assertFalse(_dates_compatible(date3, precision3, date7, precision7))
        self.assertFalse(_dates_compatible(date4, precision4, date7, precision7))
        self.assertTrue(_dates_compatible(date5, precision5, date7, precision7))
        self.assertFalse(_dates_compatible(date6, precision6, date7, precision7))
        self.assertTrue(_dates_compatible(date7, precision7, date7, precision7))
        date8, precision8 = _parse_date('2005-10-04')
        self.assertFalse(_dates_compatible(date8, precision8, date7, precision7))



if __name__ == '__main__':
    unittest.main()

