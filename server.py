from twisted.protocols import amp
from node import KeyNotHere 

class Get(amp.Command):
    arguments = [('key', amp.String())]
    response = [('value', amp.String())]
    errors = {KeyNotHere: 'KEY_NOT_HERE'}

class Find(amp.Command):
    arguments = [('key', amp.String())]
    response = [('node', amp.String())]

class RevealYourself(amp.Command):
    arguments = []
    response = [('hash', amp.String())]

class Proto(amp.AMP):
    me = None

    @classmethod
    def init(cls, me):
        cls.me = me

    def get(self, key):
        print 'Request for key %s' % key
    #    return {'value': }
    Get.responder(get)

    def find(self, key):
        pass
    Find.responder(find)

    def reveal(self):
        return {'hash': self.me}
    RevealYourself.responder(reveal)

if __name__ == '__main__':
    from twisted.internet import reactor
    from twisted.internet.protocol import Factory
    from args import parse_server
    from node import Node, Hash
    from hashlib import sha1
    args = parse_server()
    h = Hash(sha1(args.address).hexdigest())
    n = Node(h, h.prev())
    Proto.init(n)
    pf = Factory()
    pf.protocol = Proto
    reactor.listenTCP(args.port, pf)
    print 'listening on port %d' % args.port
    reactor.run()
