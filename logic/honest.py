from random import randint
from collections import Counter

# this bot will never bet what it doesnt have in its stash
# if this bot can't bet, it challenges instead

# to make bet, returned value must be dict of form {'num_dice':num_dice, 'value':value}
# to make challenge, {'challenge': True}
def turn(state, stash, gameboard):

    num_dice = gameboard['previous_bet']['num_dice'] + 1
    most_common = Counter(stash).most_common(1)[0]
    # challenge the previous player if we dont have enough die
    if most_common[1] < num_dice:
        return {'challenge': True}
    # otherwise, make a bet
    value = most_common[0]
    return {'num_dice': num_dice, 'value': value}
