from gamesdb import DataBase
from optimizer import Optimizer

def main():
    db = DataBase('games.db')
    results = db.load_game_results()
    optimizer = Optimizer(results)
    optimizer.run()
    optimizer.normalize_by_max(3000)
    results = optimizer.results()
    players = db.load_players()
    for iplayer, rating in results:
        print(players[iplayer], rating)

if __name__ == '__main__':
    main()
