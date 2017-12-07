from random import randint

# bet-making function
def turn(stash, gameboard):
    # add logic for turns here
    # to make bet, returned value must be dict of form {'num_dice':num_dice, 'value':value}
    # to make challenge, {'challenge': True}

    num_dice = gameboard['previous_bet']['num_dice'] + 1
    value = 0
    return {'num_dice': num_dice, 'value': value}
