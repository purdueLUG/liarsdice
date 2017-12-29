# Liar's Dice

This project is a  game server we created for a club activity in which
participants program bots to compete in a game of [liar's dice](https://en.wikipedia.org/wiki/Liar's_dice). 

## Installation and Setup
Example client setup

    pip install -r requirements_client.txt
    python client.py [server ip] [botname] --logic example

Server setup

    pip install -r requirements_server.txt
    crossbar start

## Running your own bot

1.  Copy `logic/example.py` to `logic/mylogic.py`.
2.  Modify `mylogic.py` with your bot's custom logic.  This code is called every time it is your bot's turn.  See below for some example input.
3.  Connect to the master server:

        python client.py liarsdice.purduelug.org [bot_name] --logic mylogic
    
You can view the game's GUI [here](http://liarsdice.purduelug.org)
      
## Arguments example
#### stash
This is a list of the dice currently under your cup.  The other bots can't see this.

      [1,1,2,2,3]

#### gameboard
This is a dictionary containing public information about the gameboard.  The most important of these is `previous_bet`.

      { 'player_list': ['hank', 'peggy', 'bobby'],
        'active_players': ['hank', 'peggy'], 
        'wins': {'hank':1, 'peggy':5, 'bobby':2 }, 
        'previous_bet': { 'num_dice':4, 'value':4 }, 
        'stash_sizes': {'hank':5, 'peggy':3}, 
        'winning_player': 'hank', 
        'current_player':'hank', 
        'previous_player':'peggy', 
        'stashes': {'hank':None, 'peggy':None},
        'session_ids': {'hank':123123123, 'peggy':231231231, 'bobby':321321321}
      } 
    
- `player_list` - a list of all currently connected players
- `active_players` - a list of all players that still have dice
- `winning_player` - the winner of the round
- `current_player` - the player whose turn it is
- `previous_player` - the previous player who might be challenged by the current player. `None` if your bot is the first in the current round
- `stashes` - a dictionary of stashes, all stashes are hidden (None) until the end of the round
- `session_id` - used by the GUI for bookkeeping purposes
- `wins` - a dictionary of how many wins each player has
