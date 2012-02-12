from twisted.internet import reactor, defer
from twisted.internet.protocol import ClientCreator
from twisted.protocols import amp
from args import parse_client
import commands

def addcall(addr, port, obj, **kwargs):
    d = ClientCreator(reactor, amp.AMP).connectTCP(addr, port)
    d.addCallback(lambda p: p.callRemote(obj, **kwargs))
    def done(res):
        print "Got result: ", res
    d.addCallback(done)
    return d


if __name__ == '__main__':
    args = parse_client()
    r = addcall(args.address, args.port, commands.Get, key = '1')
    r = addcall(args.address, args.port, commands.RevealYourself)
    reactor.run()

