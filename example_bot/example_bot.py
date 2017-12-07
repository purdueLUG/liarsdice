#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import asyncio
import time
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from autobahn.wamp.exception import ApplicationError
import importlib
import logic

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


        # call register function so server knows about me
        registered = False
        print("Waiting for server response...", end='', flush=True)
        while not registered:
            try:
                await self.call('server.login', bot_name)
                registered = True
                print("Logged in to server")
            except(ApplicationError):
                time.sleep(1)
                print('.', end='', flush=True)
        print('Connected')

        # callback function for when it's our turn
        def _turn(stash, gameboard):
            importlib.reload(logic)
            return logic.turn(stash, gameboard)
        await self.register(_turn, bot_name + '.turn')

        # callback function for server messages
        def server_console(message):
            print("Server says: {}".format(message))
        await self.subscribe(server_console, 'server.console')

        # game board subscription
        # uncomment if you want continuous game board updates
        # def store_gameboard(gameboard):
        #     self.gameboard = gameboard
        #     print("Got gameboard: {}".format(gameboard))
        # await self.subscribe(store_gameboard, 'server.gameboard')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("server_ip", help="IP address of the WAMP server")
    parser.add_argument("player_id", help="Player's unique nickname")
    args = parser.parse_args()
    bot_name = args.player_id
    runner = ApplicationRunner('ws://{}:8080/ws'.format(args.server_ip), 'realm1')
    runner.run(MyComponent)
