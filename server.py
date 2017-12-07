from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.stdio import StandardIO
from twisted.internet import defer

from autobahn.twisted.util import sleep
from autobahn.twisted.wamp import ApplicationSession
from autobahn.wamp.exception import ApplicationError
from autobahn.wamp.types import RegisterOptions

from random import randint
from itertools import cycle
import copy
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
fh = logging.FileHandler('server.log')
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

    def lose(self):
        self.stash_size -= 1
        if self.stash_size > 0:
            return False
        return True

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
        self.players.remove(player)

    def penalize(self, player):
        player.stash_size -=1
        if player.stash_size <= 0:
            self.remove(player)

    def roll(self, reset=False):
        for p in self.players:
            if reset:
                p.stash_size = 5
            p.roll()


class AppSession(ApplicationSession):
    players         = []
    previous_bet    = {'num_dice': 0, 'value': 0}
    previous_player = None
    current_player  = None
    winning_player = None
    active_players_cycle  = PlayerList([])
    reveal_stashes = False

    def assemble_gameboard(self):

        gameboard = {
            'stash_sizes'     : {p.player_id: p.stash_size for p in self.active_players_cycle.players},
            'player_list'     : [p.player_id for p in self.players],
            'previous_player' : self.previous_player.player_id if self.previous_player else None,
            'current_player'  : self.current_player.player_id if self.current_player else None,
            'previous_bet'    : self.previous_bet,
            'stashes'         : {p.player_id: p.stash if self.reveal_stashes else None for p in self.active_players_cycle.players},
            'active_players'  : [p.player_id for p in self.active_players_cycle.players],
            'wins'            : {p.player_id: p.wins for p in self.active_players_cycle.players},
            'winning_player'  : self.winning_player.player_id if self.winning_player else None,
            'session_ids'     : {p.player_id: p.session_id for p in self.players},
        }
        return gameboard

    def publish_gameboard(self):
        gameboard = self.assemble_gameboard()
        self.publish('server.gameboard', gameboard)

    def publish_console(self, message):
        self.publish('server.console', message)

    def publish_winner(self, playerID):
        self.publish('server.gameboard', playerID)

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

        log.info('Server started')

        # authentication all bot actions
        def action_authorize(session, uri, action, options):
            log.info('uri:{}'.format(uri))
            log.info('action:{}'.format(action))
            log.info('session:{}'.format(str(session)))

            allow = False
            if action == 'call':
                # dont let bots login twice
                if uri == 'server.login' and session['session'] not in [p.session_id for p in self.players]:
                    allow = True
                else:
                    log.info("bot with session id {} is already logged in".format(session['session']))
                # allow access to publication history
                if uri == 'wamp.subscription.get_events':
                    allow = True

            # force bots to register turn function with format player_id.turn
            elif action == 'register':
                for p in self.players:
                    if session['session'] == p.session_id:
                        break
                if uri.lstrip(p.player_id) == '.turn':
                    allow = True
                else:
                    log.info("bot with session_id {} tried to register invalid turn function {}".format(session['session'], uri))
            # bots may only subscribe to server gameboard and console publications
            elif action == 'subscribe':
                if uri == 'server.gameboard' or uri == 'server.console':
                    allow = True
                else:
                    log.info("bot with session_id {} is not allowed to subscribe to {}".format(session['session'], uri))
            return {"allow": allow, "disclose": True, "cache": True}

        yield self.register(action_authorize, 'server.authorize')

        # register remote procedure call named reg
        def login(player_id, session_details=None):
            # if the player id is already taken, return False
            if player_id in [p.player_id for p in self.players]:
                self.publish_console("{} tried to login, but the player_id is taken".format(player_id))
                return False
            self.players.append(Player(player_id, session_details.caller))
            self.publish_gameboard()
            self.publish_console("{} successfully logged in".format(player_id))
            return True

        yield self.register(login, 'server.login', options=RegisterOptions(details_arg='session_details'))

        # handle player disconnects
        self.subscribe(self.client_left, 'wamp.session.on_leave')
        # handle client connects
        self.subscribe(self.publish_gameboard, 'wamp.session_on_join')

        # run game forever
        while True:

            # setup phase
            self.winning_player = None
            self.current_player = None
            self.previous_player = None
            # we should sleep until len(self.players) > 2
            yield sleep(10)

            self.active_players_cycle = PlayerList(copy.copy(self.players))
            # roll all dice
            self.active_players_cycle.roll(reset=True)

            # loop players endlessly until 0 or 1 players left
            for self.current_player in self.active_players_cycle:

                # publish the game board
                yield self.publish_gameboard()

                # ask for bet:
                try:
                    player_response = yield self.call(self.current_player.player_id+'.turn',
                                                      self.current_player.stash,
                                                      self.assemble_gameboard())
                    # handle bet
                    if (isinstance(player_response, dict) and
                        'num_dice' in player_response.keys() and
                        'value' in player_response.keys() and
                        isinstance(player_response['num_dice'], int) and
                        isinstance(player_response['value'], int) and
                        player_response['num_dice'] > self.previous_bet['num_dice']):
                        self.previous_bet = player_response

                    # handle challenge
                    elif (isinstance(player_response, dict) and
                          'challenge' in player_response.keys() and
                        player_response['challenge'] == True):
                        if (not self.previous_player or
                            self.previous_player.stash.count(self.previous_bet['value']) >= self.previous_bet['num_dice']):
                            # challenge lost
                            self.publish_console(self.current_player.player_id + " lost challenge")
                            self.active_players_cycle.penalize(self.current_player)
                        else:
                            # challenge won
                            self.publish_console(self.current_player.player_id + " won challenge")
                            self.active_players_cycle.penalize(self.previous_player)
                        # reveal stashes
                        self.reveal_stashes = True
                        yield self.publish_gameboard()
                        # need to reset this for next round
                        self.previous_bet = {'num_dice': 0, 'value': 0}
                        self.active_players_cycle.roll()
                        yield sleep(1)
                        self.reveal_stashes = False

                    # invalid player response
                    else:
                        self.publish_console(self.current_player.player_id + " made an invalid response: {}".format(player_response))
                        self.active_players_cycle.penalize(self.current_player)

                # error when calling player turn - remove them from the game completely
                except ApplicationError as e:
                    self.players.remove(self.current_player)
                    self.active_players_cycle.remove(self.current_player)

                # player win
                if len(self.active_players_cycle) == 1:
                    self.reveal_stashes = True
                    yield self.publish_gameboard()
                    self.winning_player = self.active_players_cycle.players[0]
                    self.publish_console("{} won".format(self.winning_player.player_id))
                    self.winning_player.wins += 1
                    yield self.publish_gameboard()
                    self.reveal_stashes = False
                    break

                self.previous_player = self.current_player

                yield sleep(.5)
                yield self.publish_gameboard()


from autobahn.twisted.wamp import ApplicationRunner
# r = ApplicationRunner(url=u'ws://localhost:8080/ws', realm=u'realm1')
# r.run(AppSession, auto_reconnect=True, start_reactor=True)

if __name__ == '__main__':
    print("Don't start this script direclty. Start using `crossbar start`")
