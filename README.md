Liar's Dice
=

This project is a  game server we created for a club activity in which
participants program bots to compete in a game of [liar's
dice](https://en.wikipedia.org/wiki/Liar's_dice). 

Rules
-
### Setup
Our game server is manned. The game master opens up a game,
The game master initiates the setup phase. During the setup phase, we register
each player, until the game master indicates that the setup phase is complete.

### Winning conditions
The winner is the last player who possesses dice.

### Gameplay
Each player has a set of dice, called a stash, where the collective set of
players' stashes
The game is played in rounds. Players take turns issuing bets, each b

## Skeleton Bot
We've provided a skeleton "bot" for participants to modify. It is invoked with
the IP address of the WAMP server and the bot's nickname:

	$ ./skel_bot.py -h
	usage: skel_bot.py [-h] server_ip player_id
	
	positional arguments:
	  server_ip   IP address of the WAMP server
	  player_id   Player's unique nickname
	
	optional arguments:
	  -h, --help  show this help message and exit




server TODO:
nicer registration period
timeout
-starting player for next round
onleave, remove player from game

skelbot TODO:
commandline options
