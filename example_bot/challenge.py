# add logic for challenges here
# available variables are stash, gameboard, num_dice, and value
# valid return values are True and False

total_dice = sum(gameboard['stash_sizes'].values())
if gameboard['previous_bet']['num_dice'] > total_dice / 3:
    return True
else:
    return False
