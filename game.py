import calendar
import datetime
import re

class PGNSyntaxError(Exception):
    pass

_DATE = re.compile(r'(\d\d\d\d|\?+)[\-\.](\d\d|\?+)[\-\.](\d\d|\?+)')
_RESULT_STR = ('0-1', '1-0', '1/2-1/2')


def _parse_date(date_str):
    date_match = _DATE.match(date_str)
    precision = 0

    try:
        day = int(date_match.group(3))
    except ValueError:
        day = 1
        precision = 1

    try:
        month = int(date_match.group(2))
    except ValueError:
        month = 1
        precision = 2

    try:
        year = int(date_match.group(1))
    except ValueError:
        year = 2000
        precision = 3

    date = int(calendar.timegm(datetime.datetime(year, month, day).timetuple()))
    return date, precision


def lastname_from_name(name):
    i = name.find(',')
    if i >= 0:
        return name[:i]
    else:
        return name


class Game(object):

    def __init__(self, result, player1_name, player2_name,
                 player1_id=None, player2_id=None, date=None,
                 date_precision=0, moves=None, gameid=None,
                 tags=None):
        self.result = result
        self.player1_name = player1_name
        self.player2_name = player2_name
        self.player1_id = player1_id
        self.player2_id = player2_id
        if type(date) is str:
            self.date, self.date_precision = _parse_date(date)
        else:
            self.date = date
            self.date_precision = date_precision
        self.moves = moves
        self.gameid = gameid
        if tags:
            self.tags = tags
        else:
            self.tags = {}

    @staticmethod
    def fromtags(tags, moves):
        date, precision = _parse_date(tags['Date'])

        player1_name = tags['White']
        player2_name = tags['Black']

        if tags['Result'] == '1-0':
            result = 1
        elif tags['Result'] == '0-1':
            result = 0
        else:
            result = 2

        return Game(result=result,
                    player1_name=player1_name,
                    player2_name=player2_name,
                    date=date,
                    date_precision=precision,
                    moves=moves,
                    tags=tags)

    def __str__(self):
        game_str = '{} {}-{} {} ({} moves)'.format(
            _RESULT_STR[self.result],
            self.player1_name,
            self.player2_name,
            self.date_str(),
            len(self.moves) / 2)
        if self.gameid:
            return '#{}: '.format(self.gameid) + game_str
        else:
            return game_str

    def date_str(self):
        date = datetime.date.fromtimestamp(self.date)

        if self.date_precision == 0:
            return date.isoformat()

        if self.date_precision == 1:
            return '{:04}-{:02}-??'.format(date.year, date.month)

        if self.date_precision == 2:
            return '{:04}-??-??'.format(date.year)

        return '????-??-??'

    def moves_str(self):
        return ' '.join(self.moves)

    def add_tag(self, name, value):
        self.tags[name] = value

    def player1_lastname(self):
        return lastname_from_name(self.player1_name)

    def player2_lastname(self):
        return lastname_from_name(self.player2_name)



_TAG_LINE = re.compile(r'\s*\[(\w+)\s+"(.*)"\]\s*')
_SPLIT_MOVES = re.compile(r'([()]|\s+)')
_MOVE = re.compile(
    r'^(O-O(?:-O)?|[PNBRQK]?[a-h]?[1-8]?x?[a-h][1-8])(?:$|[^a-z].*)')

class PGNParser(object):

    def __init__(self, file):
        self._file = file
        self._current_line = None
        self._in_comment = False

    def parse(self):
        while not self._eof():
            try:
                tags = self._parse_tags()
                moves = self._parse_moves()
                game = Game.fromtags(tags, moves)
            except Exception:
                continue
            yield game

    def parse_all(self):
        return list(self.parse())

    def _read_line_wo_comments(self):
        line = self._file.readline()
        if line == '':
            return None
        if line[0] == '%':
            return ''

        tail = line.strip()
        output = ''
        while len(tail):
            if self._in_comment:
                p = tail.find('}')
                if p == -1:
                    tail = ''
                else:
                    tail = tail[p+1:]
                    self._in_comment = False
            else:
                semicolon = tail.find(';')
                brace = tail.find('{')

                if semicolon > -1 and (semicolon < brace or brace == -1):
                    output += tail[:semicolon]
                    tail = ''
                elif brace > -1 and (brace < semicolon or semicolon == -1):
                    output += tail[:brace] + ' '
                    tail = tail[brace+1:]
                    self._in_comment = True
                else:
                    output += tail
                    tail = ''

        return output.rstrip()

    def _next_line(self):
        if self._current_line is not None:
            line = self._current_line
            self._current_line = None
        else:
            line = self._read_line_wo_comments()

        return line

    def _push_back_line(self, line):
        if self._current_line is not None:
            raise Exception
        self._current_line = line

    def _eof(self):
        line = self._next_line()
        if line is None:
            return True
        self._push_back_line(line)
        return False

    def _parse_tags(self):
        tags = {}
        while not self._eof():
            line = self._next_line()
            if len(line) == 0:
                continue
            if line[0] != '[':
                self._push_back_line(line)
                break
            match = _TAG_LINE.match(line)
            if not match:
                raise PGNSyntaxError('Wrong tag line.')
            name, value = match.groups()
            if name in tags:
                raise PGNSyntaxError('Duplicate tag.')
            value = re.sub(r'\\([\\"])', r'\1', value)
            tags[name] = value

        return tags

    def _parse_moves(self):
        moves_str = ''
        while not self._eof():
            line = self._next_line()
            if line == '':
                continue
            if line[0] == '[':
                self._push_back_line(line)
                break
            moves_str += ' ' + line

        return self._extract_moves(moves_str)

    def _extract_moves(self, moves_str):
        moves = []
        nested = 0
        for substr in _SPLIT_MOVES.split(moves_str):
            if substr.strip() == '':
                continue
            if substr == '(':
                nested += 1
            elif substr == ')':
                nested -= 1
            elif nested == 0 and substr[0].isalpha():
                moves.append(self._strip_move(substr))
        return moves

    def _strip_move(self, move_str):
        match = _MOVE.match(move_str)
        move = match.group(1)
        if move[0] == 'P':
            move = move[1:]
        return move
