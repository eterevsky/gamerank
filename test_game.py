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

TEST_PGN3 = """
[Event "Bundesliga 0607"]
[Site "Germany"]
[Date "2007.03.31"] ; Ignore this brace: {
[Round "14.4"]
[White "Carlsen, Magnus"]  ; And this: }
[Black "Hracek, Zbynek"] {Ignore this semicolon: ;}
[Result "1-0"] ; Ignore this too
% Ignore this line
[WhiteElo "2698"]
[BlackElo "2614"]
[ECO "D58"]

1. d4 Nf6 2. c4 e6 3. Nf3 d5 4. Nc3 Be7 5. {Ignore this semicolon: ;} Bg5 O-O 6.
e3 h6 7. Bh4 b6 8. Bd3  Bb7 9. O-O dxc4 ({Eine Nebenvariante des Tartakower-
Systems: Schwarz aktiviert  den Bb7, strebt mittels ...Ne4 Leichtfigurentausch
an und hofft, sich mit  baldigem ...c5 befreien zu können.} 9... Nbd7 {ist die
oft erprobte  Hauptvariante. Hierzu kurz ein älteres, aufregendes Bundesliga-
Gefecht des  Tschechen} {sowie eine aktuelle, solide Partie:} 10. Qe2 c5 ; This
is a comment: 11. Rad2 11. Rad1 (11. Bg3  Ne4 12. cxd5 exd5 13. Rad1 Qc8 14. Rc1
Rd8 15. Rfd1 Ndf6 16. Ne5 Qe6 17. Bh4  Rac8 18. f3 cxd4 19. exd4 Nxc3 20. Rxc3
Rxc3 21. bxc3 Nd7 22. Bxe7 Qxe7 23. {Semicolon: ;} Nxd7 Rxd7 24. Re1 Qxe2 25.
Rxe2 Kf8 26. Re3 Re7 27. Kf2 Rxe3 28. Kxe3 Ke7 {  1/2-1/2 Bacrot,E
(2705)-Ivanchuk,V (2750)/Odessa 2007/CBM 116}) 11... Ne4 12.  Bg3 Nxg3 13. hxg3
cxd4 14. exd4 dxc4 15. Bxc4 Nf6 16. Ne5 Bb4 17. f4 Bxc3 18.  bxc3 Ne4 19. f5
exf5 20. Nxf7 Rxf7 21. Rxf5 Nf6 22. Rxf6 gxf6 23. Qh5 Qe7 24.  Qg6+ Kf8 25. Rf1
Be4 26. Qxh6+ Ke8 27. Re1 f5 28. Rxe4 Qxe4 29. Qg6 Rc8 30.  Qxf7+ Kd8 31. Be6
Qe3+ {  1/2-1/2 Speelman,J (2603)-Hracek,Z (2610)/Germany 2001/CBM 87}) 10. Bxc4
Ne4 11. Nxe4 ({I} 11. Bg3 $5 Nxg3 12. hxg3 c5 (12... Nd7 {/c5}) 13. d5 exd5 14.
Bxd5 Nc6 15. Qa4 Qc7 16. Rfd1 a6 (16... Rad8) 17. Qf4 $5 $14 {1-0 Van Wely,L
(2676)-Borriss,M (2455)/BL 0607 SF Berlin - SG Köln Porz 2007 (40)}) ({II} 11.
Bxe7 $6 Qxe7 12. Rc1 (12. Nxe4 Bxe4 $11) 12... Nxc3 13. Rxc3 Rc8 14. Qe2 c5 15.
Rfc1 cxd4 16. Nxd4 Nc6 17. Nxc6 Rxc6 18. Ba6 {  1/2-1/2 Unzicker,W
(2437)-Spassky,B (2548)/Mainz 2005/CBM 107 ext}) 11... Bxe4  12. Bg3 Nd7 13. Qe2
({Zu beachten ist} 13. Rc1 {/} Bd6 14. Bb5 Bxg3 15. hxg3  c5 16. Qa4 $1 {S.
Atalik/CBM} (16. Bxd7 $2 Qxd7 17. dxc5 Qb7 18. Qe2 Rfd8 $132)  ) 13... Bd6 14.
Rfd1 Qe7 15. Bb5 Rad8 16. Rac1 Bxg3 17. hxg3 c5 18. Nd2 Bd5 $6  ({Verfehlte
Provokation, nach} 18... Ba8 $142 19. Bxd7 Rxd7 20. dxc5 bxc5 $13 {  /= stünde
Schwarz völlig okay.}) 19. e4 Ba8 20. Bxd7 Qxd7 (20... Rxd7 $142 21.  dxc5 bxc5
22. Nb3 Rxd1+ 23. Rxd1 Rc8 24. Rc1 $14 {/=}) 21. dxc5 bxc5 22. Nb3  Qa4 23. Rxd8
(23. Nxc5 $142 $14) 23... Rxd8 24. Nxc5 Qxa2 25. Qb5 Kh7 {  Entlastet die
Grundreihe und plant Rd2.} 26. f3 Rd2 27. Na4 Rd4 $6 ({  Der taktisch äußerst
versierte "Fritz" empfiehlt} 27... f5 $1 {  , um den ausgesperrten Ba8 zurück
ins Spiel zu holen:} 28. exf5 a6 $1 29. Qe8 (  29. Qxa6 $4 Rxb2) (29. Qb4 Rc2 $1
30. Rxc2 (30. Rd1 exf5) 30... Qb1+ 31. Rc1  Qxc1+ 32. Kh2 exf5 $11) 29... exf5
$11) 28. Nc3 Qc4 29. Qxc4 Rxc4 30. Ra1 Rc7  31. Nb5 Rb7 32. Nd6 Rd7 33. Ra6 {In
diesem für ihn unerquicklichen Endspiel  wählt Schwarz unter Bauernopfer eine
mutige Fortsetzung, welche die  Leichtfiguren tauscht und ihm einen
Turmendspiel-Typus mit besseren  Remischancen verschafft.} Bb7 $5 ({Unter dem
sofortigen Einschalten von} 33...  h5 $5 {war das gleich thematische Endspiel
auch gut zu erreichen:} 34. b4 (34.  Kf2 Bb7 $5 35. Rxa7 Rxd6 36. Rxb7 Rd2+ 37.
Kf1 Kg6 $14) 34... Kg6 35. Kf2 (35.  Nc4 Rb7 36. Ne5+ (36. b5 Rxb5 37. Rxa7 Bc6
38. Re7 Kf6 39. Rc7 Rc5 40. Nd6 Rc2  41. Rxf7+ Ke5 42. Nb7 Bxb7 43. Rxb7 g6 $14)
36... Kf6 37. Nd3 Rd7 38. Nc5 Rc7  39. Kf2 Bc6 $14) 35... Bb7 $5 (35... f6 $2
36. Nb5 Rb7 37. Nd4 Rxb4 38. Nxe6  Rb7 39. Rd6 Re7 (39... Rb6 $2 40. Nf4+ Kh7
41. Rxb6 axb6 42. Nxh5) 40. Nf4+ Kf7  41. Nxh5 $16) 36. Rxa7 Rxd6 37. Rxb7 Rd2+
$14) 34. Rxa7 Rxd6 35. Rxb7 Rd1+ 36.  Kf2 Rd2+ 37. Kf1 Kg6 (37... h5 $5 {war
immer noch möglich, z.B.} 38. b4 (38.  Rxf7 Rxb2 39. Re7 Rb6 40. Kf2 (40. Kg1
Kg6 41. e5 Kh7 42. Kh2 Kg8 43. Kh3 Kf8  44. Rd7 Rb5 45. f4 Rb2 $14) 40... Kg6
41. e5 Kh7 42. Kg1 (42. Ke3 Kg8 43. Rd7 (  43. f4 Kf8 44. Rd7 Rb2 45. Rd2 Rb3+
46. Rd3 Rb2 $14) (43. Kf4 $6 Kf8 44. Rd7  Rb2) 43... Rb2 44. Rd2 Rb4 $14)) 38...
Kg6 39. b5 Rb2 40. b6 Kf6 41. Rb8 (41.  Ke1 Rxg2 42. Rc7 Rb2 43. b7 g5 $11) (41.
f4 Rb3 42. Kg1 Rb4 43. e5+ Kg6 44. Rb8  Kf5 45. Kh2 f6 46. b7 Rb1 $11) 41... Ke5
42. b7 g6 43. Ke1 f5 $5 44. f4+ Kxe4  45. Re8 Rxb7 46. Rxe6+ Kd4 47. Rxg6 h4 48.
gxh4 Ke3 49. Kd1 Rd7+ 50. Kc1 Rc7+  51. Kb1 Kxf4 $11) 38. g4 $1 {  Verbessert
die Mobilität der weißen Königsflügelbauern.} Kf6 (38... e5) 39. b4  Rb2 40. b5
Rb1+ 41. Kf2 Rb2+ 42. Kg3 $6 ({  Chancenreich war der Marsch zum b-Bauern:} 42.
Ke3 $5 Rxg2 43. Kd4 (43. b6 e5  44. Rd7 Rb2 45. b7 g6 46. Kd3 h5 47. Kc4 h4 48.
Kc5 h3 49. Rd6+ Kg7 50. Rb6  Rxb6 51. Kxb6 h2 52. b8=Q h1=Q 53. Qxe5+ $14) (43.
e5+ $6 Kxe5 44. Rxf7 Rb2 $11  (44... g5)) 43... e5+ $1 (43... g6 $2 44. e5+ Kg7
45. Ra7 Rb2 (45... h5 46.  gxh5 gxh5 47. Ra1 (47. Ra4 h4) 47... Rb2 48. Kc5 h4
49. Rh1 Rc2+ 50. Kb6 Rc4  51. Ka5 Rc5 52. Rxh4 Rxe5 53. Ka6 $18) 46. Kc5 h5 47.
gxh5 gxh5 48. Ra4 Rc2+  49. Kd6 Rb2 50. Kc6 Rc2+ 51. Kb7 $18) (43... Rb2 $2 44.
e5+ $1 Kg6 (44... Kg5  45. Kc5) 45. Kc5 $18) 44. Kc5 Rc2+ ({Jedoch nicht} 44...
g6 $2 45. Rc7 $1 Rc2+  46. Kb6 Rb2 (46... Rf2 47. Rc6+ Kg5 48. Kc7 Rxf3 49. b6
Rb3 50. b7 Rxb7+ 51.  Kxb7 Kxg4 52. Rf6 $18) 47. Ka6 h5 48. b6 h4 49. b7 h3 50.
Ka7 (50. Rc6+ $6 Ke7  51. Rb6 Rxb6+ 52. Kxb6 h2 53. b8=Q h1=Q 54. Qxe5+ Kf8 $14)
50... Ra2+ 51. Kb8  Kg5 52. Kc8 Rb2 53. b8=Q Rxb8+ 54. Kxb8 h2 55. Rc1 Kf4 56.
Kc7 Kxf3 57. g5 $1  Kxe4 (57... Kg4 58. Kd6 $18) 58. Kd6 $18 Kf4 59. Rh1 e4 60.
Rxh2 e3 61. Kd5)  45. Kd6 (45. Kb6 Rf2) 45... Rd2+ 46. Kc7 Rc2+ 47. Kb6 Rf2
(47... g6 $2 48. Rc7  $1 Rb2 49. Ka6 {wie vorher}) 48. Rc7 (48. Ra7 Rxf3 49. Ra5
Re3 50. Ka6 Rxe4 51.  b6 Rb4 52. b7 Rxb7 53. Kxb7 Kg5 54. Kc6 Kxg4 55. Kd5 f6
$11) 48... Rxf3 49. Rc5  (49. Rc6+ Kg5 50. Kc7 Kxg4 {und ohne den Einschub von
...g6 ist Schwarz hier  deutlich schneller als in der 44...g6?-Variante} 51. b6
Rb3 52. b7 Rxb7+ 53.  Kxb7 Kf3 $11) 49... Kg5 50. Kc6 (50. Kc7 Kxg4 51. b6 Rb3
52. Kc6 Rxb6+ 53. Kxb6  Kf4 54. Kc6 Kxe4 55. Kd6 f6 56. Ke6 Kf4) (50. Rxe5+ Kxg4
51. Kc6 f6 (51... h5  52. b6 Rf6+ 53. Kc7 Rxb6 54. Kxb6 h4 55. Re7 Kf3 56. e5
Ke4 57. Kc5 h3 58. Re8  g5 59. Kd6 g4 60. Rh8 Kf4 61. Rh7 Ke3 62. Kd5 Ke2 63.
Rxf7 g3 (63... h2 64. Rh7  g3 65. e6 $18) 64. e6 g2 65. e7 g1=Q 66. e8=Q+ $18)
52. Rc5 Rd3 (52... Re3) 53.  b6 Rd8 54. b7 Kf4 55. Kc7 Re8 56. Kb6 Rb8 57. Rc8
Rxb7+ 58. Kxb7 Kxe4 $11)  50... Kxg4 51. b6 Rf6+ 52. Kc7 Rxb6 53. Kxb6 Kf4 54.
Kc6 Kxe4 $11) 42... e5 $1  43. b6 ({Falls Weiß seinen König zum Damenflügel
zurückbeordert, erhält  Schwarz reichlich Zeit, um ein Gegenspiel mittels Kg5
plus g6 nebst f5  aufzuziehen:} 43. Kh2 g6 44. Kg1 Kg5 45. g3 f5 $5 46. gxf5
gxf5 47. exf5 Kxf5  48. b6 e4 49. Rb8 Rb1+ 50. Kf2 Rb2+ 51. Ke3 exf3 52. Kxf3
Rb3+ 53. Ke2 (53. Kg2  Kg4 54. b7 Rb2+ 55. Kf1 Kh3 $11) 53... Kg4 54. Rg8+ (54.
b7 Kh3 $11) 54... Kf5  (54... Kh5 $4 55. g4+ Kh4 56. Rg6 $18) 55. g4+ Kf6 56.
Rb8 Ke5 $1 (56... Kg5 $2  57. b7 Kh4 58. g5 $1 $18) 57. b7 Kd6 $11) 43... g6 44.
Rb8 Kg7 ({  Die eingekeilte Lage des weißen Königs war aktiv durch} 44... Kg5 $1
{  auszunutzen:} 45. Kh2 (45. b7 Rb1 (45... f6 $2 46. Kh2 Rb1 (46... Kf4 $2 47.
Rg8) 47. g3 Rb3 48. Kg2 Rb1 49. Kf2 Rb2+ 50. Ke3 Rb3+ 51. Kd2 Rb2+ 52. Kc3 Rb1
53. Kc4 Rc1+ 54. Kd5 Rd1+ 55. Ke6 Rb1 56. Kf7 Rb6 57. Kg7 Rb1 58. f4+ $1 $18
exf4 (58... Kxg4 59. Kxf6) 59. gxf4+ Kxf4 60. Kxg6 Rb6 61. Kxh6) (45... Kf6 46.
Kh2 Kg5 47. Re8 Rxb7 48. Rxe5+ Kf6 $14) 46. Re8 (46. Kf2 Kh4 $11) 46... Rxb7
47. Rxe5+ Kf6 $14) 45... Kf4 46. Rf8 (46. Rb7 Kg5 (46... f6 $2 47. Rg7 Kg5 48.
b7) 47. Rxf7 Rxb6 $14) (46. b7 $2 Rb1) 46... Rxb6 47. Rxf7+ Kg5 $14) 45. Kh2
Kf6 46. Kg1 Ke6 $2 ({Der entscheidende Fehler, die Knetmassage zeitigt endlich
Erfolg! Alternativen: I Zu spät kommt jetzt} 46... Kg5 $2 {z.B.:} 47. g3 $1 (
47. Kf1 $2 Kf4 $11) (47. b7 $2 Kf4 $14) (47. Rb7 $2 Kf4 48. Kh2 (48. Rxf7+ $2
Kg3 49. Kf1 Rxb6 $11) 48... Kg5 49. Rxf7 Rxb6 $14) 47... h5 $5 (47... Rb1+ 48.
Kf2 Rb2+ 49. Ke3 Rb3+ 50. Ke2 Kf6 51. b7 $18) 48. gxh5 Kxh5 49. Kf1 (49. b7 $2
Kg5 50. Kf1 Kf6 51. Ke1 (51. f4 Rb4 52. Kf2 (52. fxe5+ Kg5) 52... Rb3 53. Ke2
exf4 54. gxf4 Kg7 55. e5 (55. f5 gxf5 56. exf5 Kf6 $11) 55... Kh7 56. Kd2 Kg7
57. Kc2 Rb6 58. Kc3 Rb1 59. Kc4 Rc1+ 60. Kb5 Rb1+ 61. Kc6 Rc1+ 62. Kd6 Rd1+ 63.
Ke7 Rb1 $11) 51... Rb6 52. Kd2 Rb1 53. Kc3 Rb6 54. Kc4 Rb1 55. Kc5 Rc1+ 56. Kd6
Rd1+ 57. Kc7 Rc1+ 58. Kd8 Rb1 59. Ke8 Kg7 $14 60. f4 (60. Kd7 Kf6) 60... exf4
61. gxf4 Rb4 62. Kd7 Rb1 $11) (49. Rf8 $2 Rxb6 50. Rxf7 Rb1+ 51. Kf2 Rb2+ 52.
Ke3 Rb3+ 53. Ke2 Ra3 54. f4 (54. Re7 Ra5 55. Kd3 (55. Kf2 Ra2+ 56. Kf1 Ra1+ 57.
Kg2 Ra2+ 58. Kh3 Ra5 59. Rd7 Ra3 $11) 55... Ra3+ 56. Kc4 Rxf3 $11) (54. Rd7 Kg5
55. Rd3 Ra2+ 56. Ke3 Ra5 $14) (54. Rf6 Kg5 55. Re6 Ra2+ 56. Ke3 Ra3+ 57. Kf2
Ra2+ 58. Kg1 Ra1+ 59. Kh2 Ra2+ 60. Kh3 Ra5 $14) 54... exf4 55. gxf4 Ra5 $1 (
55... Kg4 $2 56. e5) 56. Rf6 Kg4 57. Ke3 Ra3+ 58. Kd4 g5 59. f5 (59. fxg5 Kxg5
$11) 59... Kf4 $11) 49... Kg5 50. Ke1 (50. b7 $2 Kf6 $11) 50... Kf6 (50... f5
51. exf5 Kxf5 52. b7 Kg5 53. f4+ $1 $18 exf4 54. gxf4+ Kg4 55. f5) 51. Kd1 Ke7
52. Kc1 Rb5 53. Kc2 Kd6 54. Rb7 $1 (54. Kc3 $2 Kc5 55. g4 Rb1 (55... Rxb6 $2
56. Rxb6 Kxb6 57. Kc4 Kc6 58. g5 $18) (55... g5 $2 56. b7 Kc6 57. Re8) 56. Rc8+
Kd6 57. Rd8+ Kc5 58. g5 (58. b7 Rxb7 59. Rd5+ Kc6 60. Rxe5 Ra7 $14) 58... Rxb6
59. Rd5+ Kc6 60. Rxe5 Kd7 $14) 54... Kc5 (54... f6 55. Rb8 Kc5 56. b7 Kc6 57.
Rf8 Rxb7 58. Rxf6+ Kc5 59. Kd3 $1 $18) 55. Rc7+ Kxb6 56. Rxf7 Kc5 57. Rd7 Kc4
58. Rd6 Ra5 59. Kd2 (59. Rxg6 $6 Ra2+ 60. Kc1 Rf2 61. Rf6 Kd4 62. g4 Ke3) 59...
g5 60. g4 $18) ({II Allein richtig war die Verfolgung} 46... Rb1+ $8 {  , und
falls Weiß einen Fortschritt erzielen will, also} 47. Kf2 {, dann} Rb2+  48. Kf1
{(Im Gegensatz zur Variante nach dem 46.Zug verfügt Weiß hier eben  nicht über
die Möglichkeit Ke3-d4 plus e5+.)} Rb1+ 49. Ke2 Rb2+ (49... Kg5 $2  50. g3) 50.
Kd3 Rxg2 {(Analyse)  und nun:} 51. Kc4 (51. Rc8 Rb2 52. Rc6+ Kg5  53. Kc4 h5 54.
gxh5 gxh5 55. Kc5 h4 56. Kd6 h3 57. Kc7 h2 58. Rc1 Rg2 $11 (  58... Kf4 $11))
(51. Ra8 Rb2 52. Ra6 Kg5 53. Kc4 h5 54. gxh5 gxh5 55. Kd5 h4  $11) 51... h5 52.
gxh5 gxh5 53. Rh8 Rb2 (53... Rc2+ 54. Kd5 $18 Rd2+ 55. Kc6  Rc2+ 56. Kd7 Rd2+
57. Kc8 Rc2+ 58. Kb8 Kg5 59. b7 Rc3 60. Ka7 Ra3+ 61. Kb6 Rxf3  62. b8=Q Rb3+ 63.
Kc6 Rxb8 64. Rxb8) 54. Kc5 (54. Rxh5 Kg6 55. Rxe5 Rxb6 $11)  54... Kg5 55. Kc6
Rc2+ 56. Kd7 Rd2+ 57. Kc8 Rc2+ 58. Kb8 f6 59. b7 Kf4 60. Rc8  Rb2 61. Kc7 Kxf3
62. b8=Q Rxb8 63. Rxb8 Kxe4 $11) 47. b7 $1 $18 {Im höheren  ne ist Schwarz jetzt
bereits verloren, da der weiße König zur entscheidenden  Wanderung gen
Damenflügel ansetzt.} Kf6 ({  In ein verlorenes Bauernendspiel führt} 47... Kd7
{nach} 48. Rf8 Rxb7 49. Rxf7+  Kc8 50. Rxb7 Kxb7 51. Kf2 Kc6 52. g5 h5 (52...
hxg5 53. Kg3 $18) 53. g3 Kc5 54.  f4 $18) 48. g3 $1 g5 ({I} 48... Kg7 49. Kf1
{nebst Königsmarsch analog dem Text  }) ({II} 48... h5 49. gxh5 gxh5 50. f4 exf4
51. e5+ Kg7 52. gxf4 $18 h4 53. f5  h3 54. f6+ Kh7 55. e6) 49. Kf1 Rb1+ 50. Ke2
Rb2+ (50... Ke7 51. Kd3 Kd7 (51...  Kf6 52. Kc4 Rc1+ 53. Kd5 Rd1+ 54. Kc6 Rc1+
55. Kd7 Rb1 56. Ke8 Kg7 57. Ke7 {  ist Zugumstellung zur Partie}) 52. Rf8 Rxb7
53. Rxf7+ Kc6 54. Rxb7 Kxb7 55. f4  $18 {ergibt wieder ein für Weiß gewonnenes
Bauernendspiel:} exf4 56. gxf4 gxf4  57. Ke2 {-f3-xf4 usw.}) 51. Kd3 Rb3+ 52.
Kc4 Rb1 53. Kc5 Rc1+ 54. Kd6 Rd1+ 55.  Kc6 Rc1+ 56. Kd7 Rb1 57. Ke8 Kg7 ({  Als
erstes, schönes Mattbild zeichnet sich nach} 57... Rb2 58. Kf8 Rb3 (58...  Kg6
59. Ke7 Kg7 60. Kd6 {siehe Partie}) 59. Rc8 Rxb7 60. Rc6# {ab.}) 58. Ke7  Rb2
59. Kd6 Kf6 ({Nach} 59... f6 {  gewinnt der Übergang ins Bauernendspiel auf
beliebige Weise:} 60. Re8 (60. Rd8  Rxb7 61. Rd7+ Rxd7+ 62. Kxd7 Kh7 63. Kd6
$18) (60. Rc8 Rxb7 61. Rc7+ Rxc7 62.  Kxc7 $18) 60... Rxb7 61. Re7+ Rxe7 62.
Kxe7 $18) {Nun jedoch gewinnt Weiß auf  spektakuläre Weise mittels
Bauerndurchbruch und Mattangriff:} 60. f4 $1 exf4 ({  Oder} 60... Rd2+ 61. Kc6
Rc2+ 62. Kd5 Rd2+ 63. Kc4 Rc2+ 64. Kd3 (64. Kb3) 64...  Rb2 65. fxe5+ Kg7 66.
Kc4 {und der König wandert nach e7 und unterstützt die  Schaffung eines weiteren
Freibauern mittels e6.}) 61. gxf4 gxf4 62. Rg8 $1 $18  {Die entscheidende
Pointe: Der Turm kann sich aus seiner passiven Lage  befreien, indem er dem
schwarzen König die Fluchtfelder auf der g-Linie nimmt  und Weiß gleichzeitig
e5# droht.} Rb6+ 63. Kc7 Rxb7+ 64. Kxb7 f3 65. Kc6 {  Das erwähnte Mattmotiv
taucht wieder auf und zwingt den schwarzen König ins  Freie.} Ke5 (65... f2 66.
Kd6 f1=Q 67. e5#) 66. Re8+ Kf4 67. Kd5 f6 (67... Kxg4  68. Rf8 $18) 68. Rf8 1-0
"""

TEST_PGN4 = """
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
[Date "1991.12.??"]
[Round "29"]
[White "Eee, Bbb"]
[Black "Fff, Ddd"]
[Result "0-1"]

1. d4 d5 0-1

[Event "F/S Return Match"]
[Site "Belgrade, Serbia JUG"]
[Date "1992.??.??"]
[Round "29"]
[White "Aaa, Bbb"]
[Black "Ccc, Ddd"]
[Result "1-0"]

1. e4 e5 1-0

[Event "F/S Return Match"]
[Site "Belgrade, Serbia JUG"]
[Date "????.??.??"]
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
        self.assertEqual(game.date_str(), '1992-11-04')

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
        self.assertEqual(games[0].date_str(), '1990-11-04')
        date1 = datetime.date.fromtimestamp(games[1].date)
        self.assertEqual(date1.isoformat(), '1990-12-05')
        self.assertEqual(games[1].date_str(), '1990-12-05')

        self.assertEqual(games[0].player1_name, 'Aaa, Bbb')
        self.assertEqual(games[0].player2_name, 'Ccc, Ddd')
        self.assertEqual(games[1].player1_name, 'Eee, Bbb')
        self.assertEqual(games[1].player2_name, 'Fff, Ddd')

        self.assertEqual(games[0].result, 1)
        self.assertEqual(games[1].result, 0)

        self.assertEqual(games[0].moves[0], 'e4')
        self.assertEqual(games[1].moves[0], 'd4')

    def test_parse3(self):
        pgn_file = io.StringIO(TEST_PGN3)
        parser = PGNParser(pgn_file)
        games = parser.parse()

        self.assertEqual(len(games), 1)
        game = games[0]

        date = datetime.date.fromtimestamp(game.date)
        self.assertEqual(date.isoformat(), '2007-03-31')
        self.assertEqual(game.date_str(), '2007-03-31')

        self.assertEqual(game.player1_name, 'Carlsen, Magnus')
        self.assertEqual(game.player2_name, 'Hracek, Zbynek')

        self.assertEqual(game.result, 1)
        self.assertEqual(len(game.moves), 135)
        self.assertEqual(game.moves[0], 'd4')
        self.assertEqual(game.moves[20], 'Nxe4')
        self.assertEqual(game.moves[134], 'Rf8')

    def test_parse_dates(self):
        pgn_file = io.StringIO(TEST_PGN4)
        parser = PGNParser(pgn_file)
        games = parser.parse()

        self.assertEqual(len(games), 4)

        self.assertEqual(games[0].date_str(), '1990-11-04')
        date = datetime.date.fromtimestamp(games[0].date)
        self.assertEqual(date.isoformat(), '1990-11-04')
        self.assertEqual(games[0].date_precision, 0)

        self.assertEqual(games[1].date_str(), '1991-12-??')
        self.assertEqual(games[1].date_precision, 1)

        self.assertEqual(games[2].date_str(), '1992-??-??')
        self.assertEqual(games[2].date_precision, 2)

        self.assertEqual(games[3].date_str(), '????-??-??')
        self.assertEqual(games[3].date_precision, 3)



if __name__ == '__main__':
    unittest.main()
