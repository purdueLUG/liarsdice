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


class Player:
    stash = []
    player_id = ''
    stash_size = 5
    wins = 0
    active = True

    def __init__(self, player_id):
        self.player_id = player_id

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

    # def next(self):

    def __iter__(self):
        while True:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            yield self.players[self.current_player_index]

    def __len__(self):
        return len(self.players)

    def remove(self, player):
        self.players.remove(player)

    def penalize(self, player):
        player.stash_size -=1
        if player.stash_size == 0:
            self.remove(player)


class AlreadyWaiting(Exception):
    pass

class PromptProtocol(LineOnlyReceiver):

    def __init__(self):
        self.callback = False

    def prompt(self, prompt: str):
        if self.callback:
            raise AlreadyWaiting
        self.transport.write((prompt + ' ').encode('utf-8'))
        self.callback = defer.Deferred()
        return self.callback

    def lineReceived(self, line: bytes):
        print("line received")
        response = line.decode('utf-8')
        self.callback(response)

class AppSession(ApplicationSession):
    players         = []
    previous_bet    = {'num_dice': 0, 'value': 0}
    previous_player = None
    current_player  = None
    winning_player = None
    active_players_cycle  = PlayerList([])

    def assemble_gameboard(self, reveal_stashes=False, winner=''):
        stashes = {}
        if reveal_stashes:
            stashes = {p.player_id: p.stash for p in self.players}

        gameboard = {
            'stash_sizes'     : {p.player_id: p.stash_size for p in self.active_players_cycle.players},
            'player_list'     : [p.player_id for p in self.players],
            'previous_player' : self.previous_player.player_id if self.previous_player else None,
            'current_player'  : self.current_player.player_id if self.current_player else None,
            'previous_bet'    : self.previous_bet,
            'stashes'         : stashes,
            'active_players'  : [p.player_id for p in self.active_players_cycle.players],
            'wins'            : {p.player_id: p.wins for p in self.players},
            'winning_player'          : self.winning_player.player_id if self.winning_player else None,
        }
        return gameboard

    def publish_gameboard(self, reveal_stashes=False, winner=''):
        gameboard = self.assemble_gameboard(reveal_stashes=reveal_stashes, winner=winner)
        self.publish('server.gameboard', gameboard)
        print("published to 'server.gameboard'")

    def publish_winner(self, playerID):
        self.publish('server.gameboard', playerID)
        print("published to 'server.gameboard'")

    @inlineCallbacks
    def onJoin(self, details):
        proto = PromptProtocol()
        StandardIO(proto, reactor=reactor)

        # register remote procedure call named reg
        def reg(ID):
            self.players.append(Player(ID))
            print("reg() called with {}".format(ID))
            self.publish_gameboard()
            return True

        yield self.register(reg, 'server.register')
        print("procedure reg() registered")

        # setup phase
        # print("ten seconds to register...")
        yield sleep(5)
        # yield proto.prompt('press enter to start')
        print("Starting")

        # run game forever
        while True:

            self.winning_player = None
            self.previous_player = None
            self.active_players_cycle = PlayerList(copy.copy(self.players))
            # roll all dice
            for p in self.players:
                p.roll()

            # loop players endlessly until 0 or 1 players left
            for self.current_player in self.active_players_cycle:

                # publish the game board
                yield self.publish_gameboard()

                if len(self.active_players_cycle) == 0:
                    print("GAME OVER, no players entered :(")
                    yield sleep(10)
                    break
                if len(self.active_players_cycle) == 1:
                    yield self.publish_gameboard(reveal_stashes=True,
                                                winner=self.active_players_cycle.players[0].player_id)
                    self.winning_player = self.active_players_cycle.players[0]
                    print("GAME OVER, winner: " + self.winning_player.player_id)
                    self.winning_player.wins += 1
                    yield self.publish_gameboard()
                    yield sleep(10)
                    break

                # ask for bet:
                try:
                    player_response = yield self.call(self.current_player.player_id+'.bet',
                                                        self.current_player.stash,
                                                        self.assemble_gameboard())
                    # handle bet
                    if ('num_dice' in player_response.keys() and
                        'value' in player_response.keys() and
                        isinstance(player_response['num_dice'], int) and
                        isinstance(player_response['value'], int) and
                        player_response['num_dice'] > self.previous_bet['num_dice']):
                        self.previous_bet = player_response

                    # handle challenge
                    elif ('challenge' in player_response.keys and
                        player_response['challenge'] == True):
                        if previous_player.stash.count(previous_bet['value']) >= previous_bet['num_dice']:
                            # challenge lost
                            self.publish('server.console', self.current_player.player_id + " lost challenge")
                            self.current_player.penalize()
                        else:
                            # challenge won
                            self.publish('server.console', self.current_player.player_id + " won challenge")
                            self.previous_player.penalize()
                        # reveal stashes
                        yield self.publish_gameboard(reveal_stashes=True)
                        # need to reset this for next round
                        self.previous_bet = {'num_dice': 0, 'value': 0}
                        yield sleep(1)

                    # invalid player response
                    else:
                        self.publish('server.console', self.current_player.player_id + " made an invalid response")
                        self.current_player.penalize()

                except ApplicationError as e:
                    self.players.remove(self.current_player)
                    self.active_players_cycle.remove(self.current_player)

                self.previous_player = self.current_player

                yield sleep(.5)
                yield self.publish_gameboard()




from autobahn.twisted.wamp import ApplicationRunner
if __name__ == '__main__':
    r = ApplicationRunner(url=u'ws://localhost:8080/ws', realm=u'realm1')
    r.run(AppSession, auto_reconnect=True, start_reactor=True)
