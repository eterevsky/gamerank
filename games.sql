CREATE TABLE game (
  gameid INTEGER PRIMARY KEY AUTOINCREMENT,
  white INTEGER,
  black INTEGER,
  result INTEGER,
  date INTEGER,
  moves TEXT,
  FOREIGN KEY (white) REFERENCES player(playerid),
  FOREIGN KEY (black) REFERENCES player(playerid)
);

CREATE TABLE player (
  playerid INTEGER PRIMARY KEY AUTOINCREMENT,
  firstnames TEXT,
  lastname TEXT
);

CREATE TABLE tag (
  game INTEGER,
  name TEXT,
  value TEXT,
  FOREIGN KEY (game) REFERENCES game(gameid)
);
