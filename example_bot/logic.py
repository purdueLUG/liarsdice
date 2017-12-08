from random import randint

# called when it's our turn
# to make bet, returned value must be dict of form {'num_dice':num_dice, 'value':value}
# to make challenge, {'challenge': True}
def turn(stash, gameboard):

    # only challenge if there is a previous player
    if gameboard['previous_player']:
        if gameboard['previous_bet']['num_dice'] > 5:
        return {'challenge': True}
    # otherwise, make a bet
    else:
        num_dice = gameboard['previous_bet']['num_dice'] + 1
        value = 0
        return {'num_dice': num_dice, 'value': value}
