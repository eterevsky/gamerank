from gamesdb import DataBase
from optimizer import Optimizer

def main():
    db = DataBase('games.db')
    results = db.load_game_results()
    players = db.load_players()
    optimizer = Optimizer(disp=True)
    optimizer.load_games(results)
    optimizer.run()
    for iplayer, rating in results:
        print(players[iplayer], rating)
        for date, r in rating:
            date = datetime.date.fromtimestamp(date * 24 * 3600)
            print(date.isoformat(), r)

if __name__ == '__main__':
    main()
