from twisted.internet.defer import inlineCallbacks

from autobahn.twisted.util import sleep
from autobahn.twisted.wamp import ApplicationSession
from autobahn.wamp.exception import ApplicationError

class AppSession(ApplicationSession):

    @inlineCallbacks
    def onJoin(self, details):

        print("Enter ID:")
        ID = input()

        ## REGISTER a procedure for remote calling
        ##
        def bet(stash, gameboard):
            new_bet = gameboard['previous_bet']
            new_bet['num_dice'] += 1
            return new_bet

        yield self.register(bet, ID+'.bet')
        print("procedure bet() registered")

        def challenge(stash, gameboard):
            print("challenge() called")
            return False

        yield self.register(challenge, ID+'.challenge')
        print("procedure challenge() registered")


        try:
            res = self.call('server.register', ID)
            print("reg() called with result: {}".format(res))
        except ApplicationError as e:
            if e.error != 'wamp.error.no_such_procedure':
                raise e

        while True:
            print("...")
            yield sleep(5)

from autobahn.twisted.wamp import ApplicationRunner
if __name__ == '__main__':
    r = ApplicationRunner(url=u'ws://localhost:8080/ws', realm=u'realm1')
    r.run(AppSession, auto_reconnect=True)
