#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from hashlib import sha1

from twisted.internet import reactor
from twisted.protocols import amp
from twisted.internet.protocol import Factory
from twisted.internet.protocol import ClientCreator
#from twisted.internet.endpoints import TCP4ServerEndpoint
#from node import KeyNotHere 


from args import parse_server
from node import Node, Hash
import commands

class Proto(amp.AMP):
    me = None

    @classmethod
    def init(cls, me):
        cls.me = me
        
    def __init__(self, node, *args, **kwargs):
        print "init"
        self.node = node
        super(Proto, self).__init__(*args, **kwargs)

    def connectionMade(self):
        print "New Connection"

    def get(self, key):
        print 'Request for key %s' % key
        print key
        key = Hash.from_hex(key)
        val = self.node.find(key)
        return {'value': val}
    commands.Get.responder(get)
    
    def set(self, key, value):
        print 'Request to set key %s' % key
        key = Hash.from_hex(key)
        val = self.node.set(key, value)
        return {'status': val}
    commands.Set.responder(set)

    def find(self, key):
        node = self.node.find_node(key)
        return {'node' : node.hash, "address" : node.address, "port" : node.port}
    commands.FindNode.responder(find)
    
    def new_node(self, key, address, port):
        node, db, stop = self.node.add_node(key, address, port)
        return {'db' : db, 'stop' : stop, 'node' : node.hash, "address" : node.address, "port" : node.port}
    commands.NewNode.responder(find)

    def new_prev(self, key, address, port):
        self.node.new_prev(key, address, port)
        return
    commands.NewPrev.responder(find)

    def reveal(self):
        print "Intorducing myself: ", self.me
        return {'hash': self.me}
    commands.RevealYourself.responder(reveal)

class ProtoFactory(Factory):
    def __init__(self, me, node=None):
        self.me = me
        self.node = node
    def buildProtocol(self, addr):
        Proto.me = self.me
        return Proto(self.node)

class Server(object):
    def __init__(self, address, port, next_address=None, next_port=None):
        self.address = address
        self.port = port
        
        self.key = Hash.from_hex(sha1(address).hexdigest())
        self.pf = ProtoFactory(str(self.key))
        if next_address and next_port:
            # server bedzie wlaczony do aktualnej sieci    
            self.make_server(next_address, next_port)
        else:
            self.node = Node(self.address, self.port, self.key, self.key.prev())
            self.pf.node = self.node
    
    def find_node(self, key, address=None, port=None):
        # find node nie moze byc wywolany jesli self.node jest node ktorego szukamy
        #
        if (address is None or port is None):
            if self.node is None:
                return # moze jakis wyjatek tu trzeba rzucic
            else:
                key, address, port = self.node.find_node(key).unpack()

        # łączymy się ze znanym węzłem w sieci i poszukujemy rekurencyjnie węzła, który zostanie 
        # naszym następnikiem
        #
        d = ClientCreator(reactor, amp.AMP).connectTCP(address, port)
        d.addCallback(lambda p: p.callRemote(commands.Find, key))
        def callback(res):
            if res['node'] == key:
                return res
            else:
                return self.find_node(key, res['address'], res['port'])
        d.addCallback(callback)
        return d


    def make_server(self, address, port):
        d = self.find_node(self.key, address, port)
        # po znalezieniu odpowiedniego wezła
        def callback(res):
            # podłączamy się do niego
            d1 = ClientCreator(reactor, amp.AMP).connectTCP(res['address'], res['port'])
            # oznajmiamy mu, że będziemy jego następnikiem
            d1.addCallback(lambda p: p.callRemote(commands.NewNode, self.key, self.address, self.port))
            def new_node(res2):
                # dostajemy jego db, i nastepnika
                self.node = Node(self.key,
                                Hash(res2['stop']), 
                                (Hash(res2['node']), res2['address'], res2['port']),
                                (Hash(res['node']), res['address'], res['key']),
                                res2['db'])

                # dodajemy node do ProtoFactory bo tego mu brakuje
                self.pf.node = self.node
                
                # kontaktujemy się z następnikiem i informujemy, że jesteśmy jego poprzednikiem
                d2 = ClientCreator(reactor, amp.AMP).connectTCP(res2['address'], res2['port'])
                d2.addCallback(lambda p: p.callRemote(commands.NewPrev, self.key, self.address, self.port))

            d1.addCallback(new_node)

        
        d.addCallback(callback)
        return d

    def run(self):
        print 'listening on port %d' % args.port
        reactor.listenTCP(self.port, self.pf)
        reactor.run()

if __name__ == '__main__':
    args = parse_server()
    server = Server(args.address, args.port)
    server.run()
    #h = Hash.from_hex(sha1(args.address).hexdigest())
    #n = Node(h, h.prev())
    #pf = ProtoFactory(str(n.start))
    #reactor.listenTCP(args.port, pf)
    #reactor.run()
