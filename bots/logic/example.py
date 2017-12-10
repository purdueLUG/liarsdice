from random import randint

# this bot always challenges if the bet size goes over 5 dice
# otherwise, it always bets on a face value of 1

# to make bet, returned value must be dict of form {'num_dice':num_dice, 'value':value}
# to make challenge, {'challenge': True}
def turn(stash, gameboard):

    # challenge if we're not the first player and if the previous bet is over 5
    if gameboard['previous_player'] and gameboard['previous_bet']['num_dice'] > 5:
            return {'challenge': True}
    # otherwise, make a bet
    num_dice = gameboard['previous_bet']['num_dice'] + 1
    value = 1
    return {'num_dice': num_dice, 'value': value}
