Liar's Dice
=

This project is a  game server we created for a club activity in which
participants program bots to compete in a game of [liar's
dice](https://en.wikipedia.org/wiki/Liar's_dice). 

Rules
-
### Setup
Example client setup
    pip install -r requirements_client.txt
    cd example_bot
    python example_bot.py [server ip] [botname]

Server setup
    pip install -r requirements_server.txt
    crossbar start

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
      
## arguments example
- stash

    [1,1,2,2,3,4]

- gameboard

    { "player_list": [ "evan", "d" ],
      "winner": "", 
      "previous_bet": { "num_dice": 4, "value": 4 }, 
      "active_players": { "evan": true, "d": true }, 
      "stash_sizes": { "evan": 5, "d": 5 }, 
      "wins": { "evan": 0, "d": 0 }, 
      "challenger_id": "evan", "player_id": "d", 
      "stashes": { "evan": [ 2, 3, 4, 5, 2 ], "d": [ 5, 5, 4, 4, 6 ] } 
    } 
    
Note that stashes is only available after a round has ended.


## Todo
- *.turn calling timeout
- prevent bots from registering .turn of other bots [see here](https://crossbar.io/docs/Authorization/)
- read in last gameboard from history on gui
