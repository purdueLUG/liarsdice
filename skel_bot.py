#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

# gameboard dict contents:
#   player_list   : list(string)             = list of fellow bot names
#   stash_sizes   : dict(string: int)        = dict of bot names and their number of dice
#   player_id     : string                   = name of the bot whose turn it is
#   challenger_id : string                   = name of challenger bot
#   previous_bet  : tuple(int, int)          = previous bet in the form (number_dice, dice_type)
#   stashes       : list(list(int))          = everybody's dice
#   game_state    : bool                     = whether game is running or not

class MyComponent(ApplicationSession):
    async def onJoin(self, details):
        # bet-making function
        def bet(my_roll, gameboard):
            # update stored game board state
            self.gameboard = gameboard
            dice_type = int(input("bet dice type: "))
            num_dice = int(input("bet number of dice: "))
            print("made bet: {} {}s".format(num_dice, dice_type)
            return (num_dice, dice_type)

        # challenge-making function
        def challenge(msg):
            response = input("make challenge? Y/n: ")
            if response == "Y" or response == "y" or response == "":
                print("bet challenged!")
                return True
            elif response == "n" or response == "N":
                print("no challenge made")
                return False

        # call register function so server knows about me
        await self.call('server.register', bot_name)
        # register my bet and challenge functions with the server
        await self.register(bet, bot_name + '.bet')
        await self.register(challenge, bot_name + '.challenge')
        print("registered self with server")

        # game board subscription
        # uncomment if you want continuous game board updates
        def store_gameboard(gameboard):
            self.gameboard = gameboard
            print("Got gameboard: {}".format(msg))
        await self.subscribe(store_gameboard, 'server.board')


if __name__ == "__main__":
    server_ip = input("server ip: ")
    bot_name = input("bot name: ")
    runner = ApplicationRunner('ws://{}:8080/ws'.format(server_ip), 'realm1')
    runner.run(MyComponent)
