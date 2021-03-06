#!/usr/bin/env python
# -*- coding: utf-8 -*-

from twisted.internet.defer import inlineCallbacks, TimeoutError
from twisted.internet import reactor
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.stdio import StandardIO
from twisted.internet import defer

from autobahn.twisted.util import sleep
from autobahn.twisted.wamp import ApplicationSession
from autobahn.wamp.exception import ApplicationError
from autobahn.wamp.types import RegisterOptions
import collections

from random import randint, shuffle
from itertools import cycle
import copy
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
fh = logging.FileHandler('server.log')
formatter = logging.Formatter('%(asctime)-15s %(message)s')
fh.setFormatter(formatter)
fh.setLevel(logging.DEBUG)
log.addHandler(fh)

class Player:
    stash = []
    player_id = ''
    stash_size = 0
    wins = 0
    active = True
    session_id = None

    def __init__(self, player_id, session_id):
        self.player_id = player_id
        self.session_id = session_id

    def roll(self):
        self.stash = [randint(1,6) for x in range(0, self.stash_size)]
        return self.stash


class PlayerList:
    def __init__(self, players):
        self.players = players
        self.current_player_index = -1

    def __iter__(self):
        while len(self.players)  > 1:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            yield self.players[self.current_player_index]

    def __len__(self):
        return len(self.players)

    def remove(self, player):
        log.debug("----------------------- b16")
        # FIXME - sometimes this fails when a player errors out
        try:
            self.players.remove(player)
        except:
            pass
        log.debug("----------------------- b17")

    def penalize(self, player):
        log.debug("----------------------- b12")
        player.stash_size -=1
        log.debug("----------------------- b13")
        if player.stash_size <= 0:
            log.debug("----------------------- b14")
            self.remove(player)
            log.debug("----------------------- b15")

    def roll(self, reset=False):
        log.debug("----------------------- a4")
        for p in self.players:
            if reset:
                p.stash_size = 5
            p.roll()
        log.debug("----------------------- a5")

    def count(self, value):
        num_dice = 0
        for p in self.players:
            num_dice += p.stash.count(value)

        return num_dice


class AppSession(ApplicationSession):
    players              = []
    previous_bet         = {'num_dice': 0, 'value': 0}
    previous_player      = None
    current_player       = None
    game_winner          = None
    round_winner         = None
    active_players_cycle = PlayerList([])
    reveal_stashes       = False
    last_wins            = collections.deque([], 50)

    def assemble_gameboard(self):

        gameboard = {
            'stash_sizes'     : {p.player_id: p.stash_size for p in self.active_players_cycle.players},
            'player_list'     : [p.player_id for p in self.players],
            'previous_player' : self.previous_player.player_id if self.previous_player else None,
            'current_player'  : self.current_player.player_id if self.current_player else None,
            'previous_bet'    : self.previous_bet,
            'stashes'         : {p.player_id: p.stash if self.reveal_stashes else None for p in self.active_players_cycle.players},
            'active_players'  : [p.player_id for p in self.active_players_cycle.players],
            'wins'            : {p.player_id: p.wins for p in self.players},
            'last_wins'       : {p.player_id: self.last_wins.count(p.player_id) for p in self.players},
            'game_winner'     : self.game_winner.player_id if self.game_winner else None,
            'round_winner'    : self.round_winner.player_id if self.round_winner else None,
            'session_ids'     : {p.player_id: p.session_id for p in self.players},
        }
        return gameboard

    # send updated gameboard to bots
    def publish_gameboard(self):
        gameboard = self.assemble_gameboard()
        self.publish('server.gameboard', gameboard)

    # send human readable text to bots
    def publish_console(self, message):
        self.publish('server.console', message)

    # tell bots when game is about to start
    def publish_game_start(self):
        log.debug("----------------------- c17")
        gameboard = self.assemble_gameboard()
        self.publish('server.game_start', gameboard)
        log.debug("----------------------- c18")

    # tell bots when game is over
    def publish_game_end(self):
        log.debug("----------------------- c15")
        gameboard = self.assemble_gameboard()
        self.publish('server.game_end', gameboard)
        log.debug("----------------------- c16")

    # tell bots when round is over
    def publish_round_end(self):
        log.debug("----------------------- c13")
        gameboard = self.assemble_gameboard()
        self.publish('server.round_end', gameboard)
        log.debug("----------------------- c14")

    # remove player from players and active_players_cycle
    def client_left(self, session_id):
        for p in self.players:
            if p.session_id == session_id:
                self.publish_console("{} left the game".format(p.player_id))
                self.players.remove(p)
                if p in self.active_players_cycle.players:
                    self.active_players_cycle.remove(p)
        self.publish_gameboard()

    @inlineCallbacks
    def onJoin(self, details):
        def foo(x):
            log.info('x:{}'.format(x))
            log.info('type(x):{}'.format(type(x)))
        yield self.register(foo, 'python3.foo')

        log.info('Server started')

        # authentication all bot actions
        def action_authorize(session, uri, action, options):
            return {"allow": True, "disclose": True, "cache": True}
            log.info('uri:{}'.format(uri))
            log.info('action:{}'.format(action))
            # log.info('session:{}'.format(str(session)))
            log.info('players:{}'.format(str(self.players)))

            allow = False
            if action == 'call':
                if uri == 'wamp.subscription.get_events':
                    allow = True
                # dont let bots login twice
                elif uri == 'server.login' and session['session'] not in [p.session_id for p in self.players]:
                    allow = True
                else:
                    log.info("bot with session id {} is already logged in".format(session['session']))
                # FIXME: allow access to publication history here

            # force bots to register turn function with format player_id.turn
            elif action == 'register':
                for p in self.players:
                    if session['session'] == p.session_id:
                        break
                if uri.lstrip(p.player_id) in ('.turn'):
                    allow = True
                else:
                    log.info("bot with session_id {} tried to register invalid turn function {}".format(session['session'], uri))
            # bots may only subscribe to server gameboard and console publications
            elif action == 'subscribe':
                if uri in ('server.gameboard', 'server.console', 'server.game_start'
                           'server.game_end', 'server.round_end'):
                    allow = True
                else:
                    log.info("bot with session_id {} is not allowed to subscribe to {}".format(session['session'], uri))
            return {"allow": allow, "disclose": True, "cache": True}

        yield self.register(action_authorize, 'server.authorize')

        # register remote procedure call named reg
        def login(player_id, session_details=None):
            # crossbar turns unicode strings into bytes.  cast it back to string
            player_id = str(player_id)
            # if the player id is already taken, return False
            if player_id in [p.player_id for p in self.players]:
                log.info("{} tried to login, but the player_id is taken".format(player_id))
                return False
            self.players.append(Player(player_id, session_details.caller))
            self.publish_gameboard()
            log.info("{} successfully logged in type {}".format(player_id, type(player_id)))
            return True

        log.debug("----------------------- foo")
        yield self.register(login, 'server.login', options=RegisterOptions(details_arg='session_details'))

        # handle player disconnects
        self.subscribe(self.client_left, 'wamp.session.on_leave')
        # handle client connects
        self.subscribe(self.publish_gameboard, 'wamp.session_on_join')

        log.debug("----------------------- start")

        # run game forever
        while True:

            # setup phase
            self.game_winner = None
            self.current_player = None
            self.previous_player = None
            # we should sleep until len(self.players) > 2
            yield sleep(1)

            log.debug("----------------------- a1")
            shuffle(self.players)
            self.active_players_cycle = PlayerList(copy.copy(self.players))
            log.debug("---------apl----------- {}".format(self.active_players_cycle.players))
            log.debug("----------pl----------- {}".format(self.players))
            log.debug("----------------------- a2")
            # roll all dice
            self.active_players_cycle.roll(reset=True)
            log.debug("----------------------- a3")

            log.debug("----------------------- a")
            self.publish_game_start()
            # loop players endlessly until 0 or 1 players left
            for self.current_player in self.active_players_cycle:
                log.debug("----------------------- b")

                # publish the game board
                self.publish_gameboard()
                log.debug("----------------------- b5")

                try:
                    # ask for bet:
                    log.debug("----------------------- b6")
                    player_response = yield self.call(self.current_player.player_id+'.turn',
                                                      self.current_player.stash,
                                                      self.assemble_gameboard()).addTimeout(1, reactor)
                    log.debug("----------------------- c")
                    # handle bet
                    if (isinstance(player_response, dict) and
                        'num_dice' in player_response.keys() and
                        'value' in player_response.keys() and
                        isinstance(player_response['num_dice'], int) and
                        isinstance(player_response['value'], int) and
                        player_response['num_dice'] > self.previous_bet['num_dice']):
                        log.debug("----------------------- c7")
                        self.previous_bet = player_response
                        self.previous_player = self.current_player

                        log.debug("----------------------- c1")
                    # handle challenge
                    elif (isinstance(player_response, dict) and
                          'challenge' in player_response.keys() and
                        player_response['challenge'] == True):
                        log.debug("----------------------- c8")
                        # self.publish_console("The bet was for {} dice.  I counted {}".format(self.previous_bet['num_dice'], self.active_players_cycle.count(self.previous_bet['value'])))
                        if (self.previous_player and
                            self.active_players_cycle.count(self.previous_bet['value']) < self.previous_bet['num_dice']):
                            log.debug("----------------------- c10")
                            # challenge won
                            self.publish_console(self.current_player.player_id + " won challenge")
                            self.round_winner = self.current_player
                            self.active_players_cycle.penalize(self.previous_player)
                            log.debug("----------------------- c4")
                        else:
                            log.debug("----------------------- c9")
                            # challenge lost
                            self.publish_console(self.current_player.player_id + " lost challenge")
                            self.round_winner = self.previous_player
                            self.active_players_cycle.penalize(self.current_player)
                            log.debug("----------------------- c3")

                        log.debug("----------------------- c5")
                        # reveal stashes
                        self.reveal_stashes = True
                        self.publish_gameboard()
                        log.debug("----------------------- c11")
                        self.publish_round_end()
                        log.debug("----------------------- c12")
                        # need to reset this for next round
                        self.previous_player = None
                        self.previous_bet = {'num_dice': 0, 'value': 0}
                        self.round_winner = None
                        self.active_players_cycle.roll()
                        # yield sleep(.1)
                        self.reveal_stashes = False
                        log.debug("----------------------- c2")

                    # invalid player response
                    else:
                        self.publish_console(self.current_player.player_id + " made an invalid response: {}".format(player_response))
                        self.active_players_cycle.penalize(self.current_player)
                    log.debug("----------------------- b1")

                # error when calling player turn - remove them from the game completely
                except ApplicationError as e:
                    log.debug("----------------------- b9")
                    log.error(e)
                    self.publish_console("{} had an error".format(self.current_player.player_id))
                    log.debug("----------------------- b10")
                    self.active_players_cycle.penalize(self.current_player)
                    log.debug("----------------------- b11")
                except TimeoutError as e:
                    log.error(e)
                    log.debug("----------------------- b8")
                    self.publish_console("{} took too long to respond".format(self.current_player.player_id))
                    self.active_players_cycle.penalize(self.current_player)
                log.debug("----------------------- b2")


                # player win
                if len(self.active_players_cycle) == 1:
                    log.debug("----------------------- b3")
                    self.reveal_stashes = True
                    self.game_winner = self.active_players_cycle.players[0]
                    self.publish_console("{} won".format(self.game_winner.player_id))
                    self.game_winner.wins += 1
                    self.last_wins.append(self.game_winner.player_id)
                    self.publish_gameboard()
                    self.publish_game_end()
                    self.reveal_stashes = False
                    log.debug("----------------------- c6")
                    break
                log.debug("----------------------- b4")


                # yield sleep(.1)
                self.publish_gameboard()

                log.debug("----------------------- b7")
            log.debug("----------------------- d")


from autobahn.twisted.wamp import ApplicationRunner
# r = ApplicationRunner(url=u'ws://localhost:8080/ws', realm=u'realm1')
# r.run(AppSession, auto_reconnect=True, start_reactor=True)

if __name__ == '__main__':
    print("Don't start this script direclty. Start using `crossbar start`")
