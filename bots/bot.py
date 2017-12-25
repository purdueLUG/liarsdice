#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from autobahn.wamp.exception import ApplicationError
from autobahn.twisted.component import Component, run
from autobahn.twisted.util import sleep
from twisted.internet.defer import inlineCallbacks
import importlib
import logic
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
            "url": u"ws://diode.purduelug.org:8080/ws",
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

    #---------- RPC -----------

    # callback function for when it's our turn
    def turn(stash, gameboard):
        importlib.import_module('logic.' + args.logic)
        return {u(key): value for key, value in getattr(logic, args.logic).turn(stash, gameboard).items()}
    yield self.register(turn, u(args.player_id + '.turn'))

    #---------- Pub/Sub -----------

    # callback function for server messages
    def server_console(message):
        print("Server says: {}".format(message))
    yield self.subscribe(server_console, u'server.console')


# handle server shutdown
@component.on_disconnect
@inlineCallbacks
def disconnect(self, was_clean):
    print("Server shutdown or connection lost")
    yield


run(component)
