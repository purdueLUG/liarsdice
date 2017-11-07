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


class Player:
    stash = []
    player_id = ''
    stash_size = 0
    wins = 0
    active = True

    def __init__(self, player_id, stash_size):
        self.player_id = player_id
        self.stash_size = stash_size

    def roll(self):
        self.stash = [randint(1,6) for x in range(0, self.stash_size)]
        return self.stash

    def lose(self):
        self.stash_size -= 1
        if self.stash_size > 0:
            return False
        return True

class PlayerList(list):
    def __init__(self, *args):
        list.__init__(self, *args)

    def roll(self):
        for p in self:
            p.roll()

    def rotate(self, n):
        '''Rotate list l to the left n places.'''
        self = self[n:] + self[:n]
        return PlayerList(self)

    def delete(self, player):
        if player in self:
            self.remove(player)

    def penalize(self, player):
        if player.stash_size > 0:
            player.lose()
        if player.stash_size <= 0:
            self.delete(player)

    def get_pool(self):
        pool = []
        for p in self:
            pool += p.stash
        return pool

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
    players          = PlayerList()
    starting_players = PlayerList()
    prev_bet         = {'num_dice': 0, 'value': 0}
    current_player   = Player('', 0)
    next_player      = Player('', 0)

    def assemble_gameboard(self, reveal_stashes=False, winner=''):
        stashes = {}
        if reveal_stashes:
            stashes = {p.player_id: p.stash for p in self.players}

        gameboard = {
            'stash_sizes'    : {p.player_id: p.stash_size for p in self.players},
            'player_list'    : [p.player_id for p in self.starting_players],
            'player_id'      : self.current_player.player_id,
            'challenger_id'  : self.next_player.player_id,
            'previous_bet'   : self.prev_bet,
            'stashes'        : stashes,
            'active_players' : {p.player_id: p in self.players for p in self.starting_players},
            'wins'           : {p.player_id: p.wins for p in self.starting_players},
            'winner'         : winner,
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
            self.starting_players += PlayerList([Player(ID, 1)])
            self.players += PlayerList([Player(ID, 5)])
            print("reg() called with {}".format(ID))
            self.publish_gameboard()
            return True

        yield self.register(reg, 'server.register', options=RegisterOptions(details_arg='session_details'))
        print("procedure reg() registered")

        # setup phase
        # print("Ten seconds to register...")
        # yield sleep(10)
        yield proto.prompt('press enter to start')
        print("Starting")

        while True:
            self.players = PlayerList(self.starting_players.copy())
            for p in self.players:
                p.stash_size = 5


            while len(self.players) > 1:
                # roll all dice
                self.players.roll()


                circle = cycle(enumerate(self.players))

                challenge_response = False
                valid_bet = True
                while challenge_response == False:
                    ind,self.current_player = next(circle)

                    # publish the game board
                    yield self.publish_gameboard()

                    # ask for bet:
                    try:
                        new_bet = yield self.call(self.current_player.player_id+'.bet',
                                                  self.current_player.stash,
                                                  self.assemble_gameboard())
                        print("bet() called on {} with result: {}".format(self.current_player, new_bet))
                        valid_nums = isinstance(new_bet['num_dice'], int) and isinstance(new_bet['value'], int)
                        if valid_nums and new_bet['num_dice'] > self.prev_bet['num_dice']:
                            valid_bet = True
                            self.prev_bet = new_bet
                        else:
                            print("bet is invalid!")
                            valid_bet = False
                            self.players.penalize(self.current_player)
                    except ApplicationError as e:
                        valid_bet = False
                        self.players.delete(self.current_player)

                    if valid_bet:
                        # ask next player for challenge
                        next_ind = (ind+1)%len(self.players)
                        self.next_player = self.players[(ind+1)%len(self.players)]
                        try:
                            challenge_response = yield self.call(self.next_player.player_id+'.challenge',
                                                                 self.next_player.stash,
                                                                 self.assemble_gameboard())
                            print("challenge() called on {} with result: {}".format(self.next_player,
                                                                                    challenge_response))
                        except ApplicationError as e:
                            self.players.delete(self.next_player)

                    yield sleep(1)
                    yield self.publish_gameboard()

                # reveal stashes
                yield self.publish_gameboard(reveal_stashes=True)

                # check the bet against the pool
                bet_value = self.prev_bet['value']
                bet_num_dice = self.prev_bet['num_dice']
                pool = self.players.get_pool()
                num_of_value = pool.count(bet_value)

                print("There were {} {}s".format(num_of_value, bet_value))

                # if the bet was good
                if bet_num_dice <= num_of_value:
                    self.publish('server.console', self.current_player.player_id + " won its bet!")
                    print("Better wins!")
                    # winner begins next round
                    self.players = self.players.rotate(ind)

                    # penalize loser
                    self.next_player.lose()
                    if self.next_player.stash_size <= 0:
                        self.players.delete(self.next_player)
                else:
                    self.publish('server.console', self.next_player.player_id + " won its challenge!")
                    print("Challenger wins!")
                    # winner begins next round
                    self.players = self.players.rotate(next_ind)

                    # penalize loser
                    self.current_player.lose()
                    if self.current_player.stash_size <= 0:
                        self.players.delete(self.current_player)

                # need to reset this for next round
                self.prev_bet = {'num_dice': 0, 'value': 0}

                yield sleep(5)

            if len(self.players) <= 0:
                print("GAME OVER, no players entered :(")
            else:
                yield self.publish_gameboard(reveal_stashes=True, winner=self.players[0].player_id)
                print("GAME OVER, winner: " + self.players[0].player_id)
                for p in self.starting_players:
                    if p.player_id == self.players[0].player_id:
                        p.wins += 1
            yield sleep(10)


from autobahn.twisted.wamp import ApplicationRunner
if __name__ == '__main__':
    r = ApplicationRunner(url=u'ws://localhost:8080/ws', realm=u'realm1')
    r.run(AppSession, auto_reconnect=True, start_reactor=True)
