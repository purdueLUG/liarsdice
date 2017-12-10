#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import asyncio
import time
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from autobahn.wamp.exception import ApplicationError
import importlib
import logic
import sys

class MyComponent(ApplicationSession):

    async def onJoin(self, details):
        logged_in = False
        while not logged_in:
            try:
                # login to gameserver
                await self.call('server.login', bot_name)
                logged_in = True
            except ApplicationError:
                pass
        print("Logged in to server")

        # callback function for when it's our turn
        def _turn(stash, gameboard):
            importlib.reload(logic)
            return getattr(logic, logic_func).turn(stash, gameboard)
        await self.register(_turn, bot_name + '.turn')

        # callback function for server messages
        def server_console(message):
            print("Server says: {}".format(message))
        await self.subscribe(server_console, 'server.console')

    # handle server shutdown
    async def onDisconnect(self):
        print("Server shutdown or connection lost")
        asyncio.get_event_loop().stop()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("server_ip", help="IP address of the WAMP server")
    parser.add_argument("player_id", help="Player's unique nickname")
    parser.add_argument('--logic', action="store_true", default='example')

    args = parser.parse_args()
    bot_name = args.player_id
    logic_function = args.logic

    while True:
        print("Connecting")
        runner = ApplicationRunner('ws://{}:8080/ws'.format(args.server_ip), 'realm1')
        # poor man's auto reconnect
        try:
            runner.run(MyComponent)
        except ConnectionRefusedError:
            print("Could not connect to server")
        time.sleep(10)
        asyncio.set_event_loop(asyncio.new_event_loop())
