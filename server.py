from twisted.protocols import amp
from node import KeyNotHere 
import commands

class Proto(amp.AMP):
    me = None

    @classmethod
    def init(cls, me):
        cls.me = me

    def get(self, key):
        print 'Request for key %s' % key
        return {'value': 'ok'}
    commands.Get.responder(get)

    def find(self, key):
        pass
    commands.Find.responder(find)

    def reveal(self):
    print "Intorducing myself: ", self.me
        return {'hash': self.me}
    commands.RevealYourself.responder(reveal)

if __name__ == '__main__':
    from twisted.internet import reactor
    from twisted.internet.protocol import Factory
    from args import parse_server
    from node import Node, Hash
    from hashlib import sha1
    args = parse_server()
    h = Hash(sha1(args.address).hexdigest())
    n = Node(h, h.prev())
    Proto.init(str(n.start))
    pf = Factory()
    pf.protocol = Proto
    reactor.listenTCP(args.port, pf)
    print 'listening on port %d' % args.port
    reactor.run()
