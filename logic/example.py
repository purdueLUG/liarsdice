from random import randint

# this bot always challenges if the bet size goes over 5 dice
# otherwise, it always bets on a face value of 1

# See the README for a description of state, stash, and gameboard

# put any state initialization code here.  called when game is about to start
def game_start(state, gameboard):
    state.my_wins = 0

# update your state variables here when the game ends
def game_end(state, gameboard):
    # if we are the winner of the game
    if gameboard['game_winner'] == state.player_id:
        state.my_wins += 1
        print('I now have {} wins'.format(state.my_wins))

# update your state variables here when the round ends
def round_end(state, gameboard):
    # if we are the winner of the round
    if gameboard['round_winner'] == state.player_id:
        print("I won the round!")

# to make bet, returned value must be dict of form {'num_dice':num_dice, 'value':value}
# to make challenge, {'challenge': True}
def turn(state, stash, gameboard):

    # challenge if we're not the first player and if the previous bet is over 5
    if gameboard['previous_player'] and gameboard['previous_bet']['num_dice'] > 5:
            print('---------------------------------------------------------------------------------')
            print('previous_bet:', gameboard['previous_bet'])
            print('stash_sizes:', gameboard['stash_sizes'])
            print('stash:', stash)
            return {'challenge': True}
    # otherwise, make a bet
    num_dice = gameboard['previous_bet']['num_dice'] + 1
    value = 1
    return {'num_dice': num_dice, 'value': value}
