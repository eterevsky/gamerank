Maximum likelihood-based ratings for games with two players
===========================================================

A standard way to determine the strength of players in a game like chess is the
Elo rating system. It is based on the assumption that the probability of winning
a game has normal distribution over the difference in players ratings. The Elo
rating of a player after a particular game depends on:

- his rating before the game,
- the rating of his opponent,
- the result of the game.

The objective of this project is to construct a better rating system, based on
less assumptions. The main principles remains the same: the expected probability
of winning in a game depends on the difference of ratings. The resulting rating
is also normalized the same way, as Elo rating, namely the difference of 200
points means the better player will win in 75% of games. (A draw is counted as
"half a win" plus "half a loss".)

The rating is a function of a player and time: `rating(p, t)`. The expected
result of the game played at the time t0 between players p0 and p1 is
`f(rating(p0, t0) - rating(p1, t0))`. The function `f` plays the role of the
normal distribution in Elo rating.

Both function `f` and the ratings themselves are determined by maximizing the
[maximum likelihood](http://en.wikipedia.org/wiki/Maximum_likelihood) of all the
predicted game results. To prevent the ratings from oscillating between +∞ and
-∞, depending on whether the player wins or looses a particular game, we
penalize the rate of change of rating over time (another possible way is to
penalize the rating change depending on the number of played games, not time).

The main difference of this ratings from traditional rating systems is that the
past ratings may change retroactively after new games are taken into account.

How to calculate the ratings
----------------------------

**Disclaimer:** This is a very raw implementation, not a stable product.

This repository contains the python implementation of this rating system. It
requires Python3, numpy and scipy to run. numexpr library will be used to speed
up the calculations if it is installed. It is known to work in reasonable time
on a dataset containing a few millions of games. It is configured to count the
time in years, meaning a player rating changes from year to year. It accepts the
databases of chess games in PGN format. The `f` function space include linear
combinations of normal and logistic distribution.

To import a PGN file use `import_pgn.py`. There is a heuristics to skip the
duplicate games. To calculate the ratings from the imported games use
`gamerank.py`. It doesn't have a lot of options just yet, so to change something
you'll have to hack.

The unittests are run by `python3 -m unittest`.

TODO
----

This method can also be applied to games with more complex rating systems,
involving handicaps. That can be done by making the `f` function dependent on
the game parameters. For Go, for instance, this will include the number of
handicap stones and [komi](http://en.wikipedia.org/wiki/Komidashi).

Sample results
--------------

... Have to calculate and add results ...
