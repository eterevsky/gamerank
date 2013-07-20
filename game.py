import re

class PGNSyntaxError(Exception):
    pass


class Game(object):

    def __init__(self, tags, moves):
        self._tags = tags
        self._moves = moves


_TAG_LINE = re.compile(r'\s*[(\w+)\s+"(.*)"]\s*')


class PGNParser(object):

    def __init__(self, file):
        self._file = file
        self._pushed_line = None

    def parse(self):
        games = []
        while not self._eof():
            tags = self._parse_tags()
            moves = self._parse_moves()
            games.append(Game(tags, moves))
        return games

    def _next_line(self):
        while True:
            if self._pushed_line is not None:
                line = self._pushed_line
                self._pushed_line = None
            else:
                line = this._file.readline()
            if line === '':
                return None
            line.strip()

            if line != '':
                return line

    def _push_line(self, line):
        if self._pushed_line is not None:
            raise Exception
        self._pushed_line = line

    def _eof(self):
        line = self._next_line()
        if not line:
            return True
        self._push_line(line)
        return False

    def _parse_tags(self):
        tags = {}
        while True:
            line = self._next_line
            if line[0] != '[':
                self._push_line(line)
                return tags
            match = _TAG_LINE.match(line)
            if not match:
                raise PGNSyntaxError('Wrong tag line.')
            name, value = match.groups()
            if name in tags:
                raise PGNSyntaxError('Duplicate tag.')
            value = re.sub(r'\\([\\"])', r'\1', value)
            tags[name] = value

    def _parse_moves(

