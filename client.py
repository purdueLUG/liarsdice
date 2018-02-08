#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from autobahn.wamp.exception import ApplicationError
from autobahn.twisted.component import Component, run
from autobahn.twisted.util import sleep
from twisted.internet.defer import inlineCallbacks
from twisted.python import log
import sys
from importlib import import_module
from six.moves import reload_module
import logic
import time
# do bytestring to unicode conversion in python2. no effect in python3
from six import u

parser = argparse.ArgumentParser()
parser.add_argument("server_ip", help="IP address of the WAMP server")
parser.add_argument("player_id", help="Player's unique nickname")
parser.add_argument('--logic', metavar='logic_function', type=str, default="example", help="logic function name (without .py)")
args = parser.parse_args()

component = Component(
    transports = [
        {
            "type": "websocket",
            "url": u"ws://{}:8080/ws".format(args.server_ip),
            "options": {
                "open_handshake_timeout": 60.0,
            }
        }
    ],
    realm=u'realm1',
)


@component.on_join
@inlineCallbacks
def join(self, details):

    logged_in = False

    while not logged_in:
        try:
            # login to gameserver
            yield self.call(u'server.login', u(args.player_id))
            logged_in = True
        except ApplicationError:
            yield sleep(5)
    print("Logged in to server")

    logic_module = import_module('logic.' + args.logic)

    # empty class for storing state
    class empty(object):
        # initialize bot state
        def __init__(self):
            self.player_id = args.player_id
            if hasattr(logic_module, 'init'):
                logic_module.init(self)

    state = empty()

    #---------- RPC -----------

    # callback function for when it's our turn
    def turn(stash, gameboard):
        reload_module(logic_module)
        return {u(key): value for key, value in logic_module.turn(state, stash, gameboard).items()}
    yield self.register(turn, u(args.player_id + '.turn'))

    #---------- Pub/Sub -----------

    # subscription for game end
    def game_end(gameboard):
        reload_module(logic_module)
        if hasattr(logic_module, 'game_end'):
            logic_module.game_end(state, gameboard)
    yield self.subscribe(game_end, u'server.game_end')

    # subscription for round end
    def round_end(gameboard):
        reload_module(logic_module)
        if hasattr(logic_module, 'round_end'):
            logic_module.round_end(state, gameboard)
    yield self.subscribe(round_end, u'server.round_end')

    # subscription for server messages
    def server_console(message):
        print("Server says: {}".format(message))
    yield self.subscribe(server_console, u'server.console')


# handle server shutdown
@component.on_disconnect
def disconnect(self, was_clean):
    print("Server shutdown or connection lost")

run(component)
