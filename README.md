Liar's Dice
=

This project is a  game server we created for a club activity in which
participants program bots to compete in a game of [liar's dice](https://en.wikipedia.org/wiki/Liar's_dice). 

Rules
-
## Installation and Setup
Example client setup
    pip install -r requirements_client.txt
    cd example_bot
    python example_bot.py [server ip] [botname]

Server setup
    pip install -r requirements_server.txt
    crossbar start

## Running your bot
Modify `example_bot/logic.py` with your bot's custom logic.  This code is called every time it is your bots turn.  Some basic example code is already provided.

Connect to the master server like so:

    python
      
## Arguments example
- stash

    [1,1,2,2,3,4]

- gameboard

    { "player_list": [ "evan", "bob" ],
      "winner": "", 
      "previous_bet": { "num_dice": 4, "value": 4 }, 
      "active_players": { "evan": true, "bob": true }, 
      "stash_sizes": { "evan": 5, "bob": 5 }, 
      "wins": { "evan": 0, "bob": 0 }, 
      "current_player": "evan", "player_id": "bob", 
      "stashes": { "evan": [ 2, 3, 4, 5, 2 ], "bob": [ 5, 5, 4, 4, 6 ] } 
    } 
    
Note that stashes is only available after a round has ended.
