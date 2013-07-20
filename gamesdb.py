import os.path
import sqlite3

import game

class DataBase(object):
    def __init__(self, path='games.db'):
        self._conn = sqlite3.connect(path)
