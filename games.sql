CREATE TABLE game (
  gameid INTEGER PRIMARY KEY AUTOINCREMENT,
  playerid1 INTEGER,
  playerid2 INTEGER,
  result INTEGER,
  date INTEGER,
  dateprecision INTEGER,
  nmoves INTEGER,
  moves TEXT,
  FOREIGN KEY (playerid1) REFERENCES player(playerid),
  FOREIGN KEY (playerid2) REFERENCES player(playerid)
);

CREATE INDEX game_moves ON game (moves);

CREATE TABLE player (
  playerid INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT,
  firstnames TEXT,
  lastname TEXT
);

CREATE INDEX player_name ON player (name);

CREATE TABLE tag (
  gameid INTEGER,
  name TEXT,
  value TEXT,
  FOREIGN KEY (gameid) REFERENCES game(gameid)
);
