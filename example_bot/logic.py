from random import randint

# bet-making function
def bet(stash, gameboard):
    # add logic for bets here
    # returned value must be dict of form {'num_dice':num_dice, 'value':value}

    num_dice = gameboard['previous_bet']['num_dice'] + 1
    value = 0
    return {'num_dice': num_dice, 'value': value}

# challenge-making function
def challenge(stash, gameboard):
    # add logic for challenges here
    # valid return values are True and False

    return False
