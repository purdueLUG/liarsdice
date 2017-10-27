#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import asyncio
import time
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from autobahn.wamp.exception import ApplicationError

# gameboard dict contents:
#   player_list   : list(string)            = list of fellow bot names
#   stash_sizes   : dict(string: int)       = dict of bot names and their number of dice.
#                                             key: player_id
#                                             value: num_dice
#   player_id     : string                  = name of the bot whose turn it is
#   challenger_id : string                  = name of challenger bot
#   previous_bet  : dict(string: int)       = previous bet in a dict of the form:
#                                             'num_dice: int' and 'value: int'
#   stashes       : dict(string: list(int)) = everybody's dice
#   game_state    : bool                    = whether game is running or not

class MyComponent(ApplicationSession):
    async def onJoin(self, details):
        # bet-making function
        def bet(stash, gameboard):
            # update stored game board state
            self.gameboard = gameboard
            print(self.gameboard)
            print(stash)
            num_dice = int(input("number of dice to bet: "))
            value = int(input("value of dice to bet: "))
            print("made bet: {} {}s".format(num_dice, value))
            return {'num_dice': num_dice, 'value': value}

        # challenge-making function
        def challenge(stash, gameboard):
            # update stored game board state
            self.gameboard = gameboard
            print(self.gameboard)
            print(stash)
            response = input("make challenge? Y/n: ")
            if response in ['Y', 'y', '']:
                print("bet challenged!")
                return True
            elif response in ['N', 'n']:
                print("no challenge made")
                return False

        # call register function so server knows about me
        registered = False
        print("Waiting for server response...", end='', flush=True)
        while not registered:
            try:
                await self.call('server.register', bot_name)
                registered = True
            except(ApplicationError):
                time.sleep(1)
                print('.', end='', flush=True)
        print('done')

        # register my bet and challenge functions with the server
        await self.register(bet, bot_name + '.bet')
        await self.register(challenge, bot_name + '.challenge')
        print("registered self with server")

        # game board subscription
        # uncomment if you want continuous game board updates
        def store_gameboard(gameboard):
            self.gameboard = gameboard
            print("Got gameboard: {}".format(gameboard))
        await self.subscribe(store_gameboard, 'server.gameboard')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("server_ip", help="IP address of the WAMP server")
    parser.add_argument("player_id", help="Player's unique nickname")
    args = parser.parse_args()
    bot_name = args.player_id
    runner = ApplicationRunner('ws://{}:8080/ws'.format(args.server_ip), 'realm1')
    runner.run(MyComponent)
