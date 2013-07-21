import datetime
import io
import unittest

from game import PGNParser


TEST_PGN1 = """
[Event "F/S Return Match"]
[Site "Belgrade, Serbia JUG"]
[Date "1992.11.04"]
[Round "29"]
[White "Fischer, Robert J."]
[Black "Spassky, Boris V."]
[Result "1/2-1/2"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3
O-O 9. h3 Nb8 10. d4 Nbd7 11. c4 c6 12. cxb5 axb5 13. Nc3 Bb7 14. Bg5 b4 15.
Nb1 h6 16. Bh4 c5 17. dxe5 Nxe4 18. Bxe7 Qxe7 19. exd6 Qf6 20. Nbd2 Nxd6 21.
Nc4 Nxc4 22. Bxc4 Nb6 23. Ne5 Rae8 24. Bxf7+ Rxf7 25. Nxf7 Rxe1+ 26. Qxe1 Kxf7
27. Qe3 Qg5 28. Qxg5 hxg5 29. b3 Ke6 30. a3 Kd6 31. axb4 cxb4 32. Ra5 Nd5 33.
f3 Bc8 34. Kf2 Bf5 35. Ra7 g6 36. Ra6+ Kc5 37. Ke1 Nf4 38. g3 Nxh3 39. Kd2 Kb5
40. Rd6 Kc5 41. Ra6 Nf2 42. g4 Bd3 43. Re6 1/2-1/2
"""

TEST_PGN2 = """
[Event "F/S Return Match"]
[Site "Belgrade, Serbia JUG"]
[Date "1990.11.04"]
[Round "29"]
[White "Aaa, Bbb"]
[Black "Ccc, Ddd"]
[Result "1-0"]

1. e4 e5 1-0

[Event "F/S Return Match"]
[Site "Belgrade, Serbia JUG"]
[Date "1990.12.05"]
[Round "29"]
[White "Eee, Bbb"]
[Black "Fff, Ddd"]
[Result "0-1"]

1. d4 d5 0-1
"""


class TestPGNParser(unittest.TestCase):

    def test_parse1(self):
        pgn_file = io.StringIO(TEST_PGN1)
        parser = PGNParser(pgn_file)
        games = parser.parse()

        self.assertEqual(len(games), 1)
        game = games[0]
        self.assertEqual(len(game.moves), 85)

        date = datetime.date.fromtimestamp(game.date)
        self.assertEqual(date.isoformat(), '1992-11-04')

        self.assertEqual(game.player1_name, 'Fischer, Robert J.')
        self.assertEqual(game.player2_name, 'Spassky, Boris V.')

        self.assertEqual(game.result, 2)

        self.assertEqual(game.moves[0], 'e4')
        self.assertEqual(game.moves[3], 'Nc6')
        self.assertEqual(game.moves[4], 'Bb5')
        self.assertEqual(game.moves[8], 'O-O')
        self.assertEqual(game.moves[19], 'Nbd7')
        self.assertEqual(game.moves[22], 'cxb5')
        self.assertEqual(game.moves[35], 'Qxe7')
        self.assertEqual(game.moves[46], 'Bxf7')
        self.assertEqual(game.moves[84], 'Re6')


    def test_parse2(self):
        pgn_file = io.StringIO(TEST_PGN2)
        parser = PGNParser(pgn_file)
        games = parser.parse()

        self.assertEqual(len(games), 2)

        date0 = datetime.date.fromtimestamp(games[0].date)
        self.assertEqual(date0.isoformat(), '1990-11-04')
        date1 = datetime.date.fromtimestamp(games[1].date)
        self.assertEqual(date1.isoformat(), '1990-12-05')

        self.assertEqual(games[0].player1_name, 'Aaa, Bbb')
        self.assertEqual(games[0].player2_name, 'Ccc, Ddd')
        self.assertEqual(games[1].player1_name, 'Eee, Bbb')
        self.assertEqual(games[1].player2_name, 'Fff, Ddd')

        self.assertEqual(games[0].result, 1)
        self.assertEqual(games[1].result, 0)

        self.assertEqual(games[0].moves[0], 'e4')
        self.assertEqual(games[1].moves[0], 'd4')



if __name__ == '__main__':
    unittest.main()
