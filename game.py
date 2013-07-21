import re

class PGNSyntaxError(Exception):
    pass


class Game(object):

    def __init__(self, tags, moves):
        self.player1 = None
        self.player2 = None
        self.tags = tags
        self.moves = moves


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
        games = []
        while not self._eof():
            tags = self._parse_tags()
            moves = self._parse_moves()
            games.append(Game(tags, moves))
        return games

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