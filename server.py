#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import hashlib

from pickle import loads, dumps

from twisted.internet import reactor
from twisted.protocols import amp
from twisted.internet.protocol import Factory
from twisted.internet.protocol import ClientCreator
#from twisted.internet.endpoints import TCP4ServerEndpoint
#from node import KeyNotHere 


from args import parse_server
from node import Node, Hash, Neighbor
import commands

class Proto(amp.AMP):
    me = None

    @classmethod
    def init(cls, me):
        cls.me = me
        
    def __init__(self, node, server, *args, **kwargs):
        self.node = node
        self.server = server
        super(Proto, self).__init__(*args, **kwargs)

    def get(self, key):
        hex_key = hashlib.sha1(str(key)).hexdigest()
        hash_key = Hash.from_str(hex_key)
        node = self.node.find_node(hash_key)
        if node.hash == self.node.start: # to my mamy ten klucz
            print "Pobrano klucz"
            val = self.node.find(hash_key)
            return {'value': val}
        else:
            d = self.server.find_node(hash_key, node.address, node.port) # szukamy odpowiedniego serwera, zwracamy deffer
            def callback(res): # res zawiera dane serwera na ktorym moze byc klucz
                # podłączamy się do niego
                d1 = ClientCreator(reactor, amp.AMP).connectTCP(res['address'], res['port'])
                d1.addCallback(lambda p: p.callRemote(commands.Get, key=key))

                def trapError(result):
                    result.trap(Exception)
                    raise result.type()
                d1.addErrback(trapError)
                
                return d1 # deffer, który zawierać będzie wynik metody get na właściwym serwerze

            d.addCallback(callback)
            return d
    commands.Get.responder(get)
    
    def set(self, key, value):
        hex_key = hashlib.sha1(str(key)).hexdigest()
        hash_key = Hash.from_str(hex_key)
        node = self.node.find_node(hash_key)
        if node.hash == self.node.start: # to my będziemy przechowywać ten klucz
            print "Zapisano klucz-wartość"
            val = self.node.set(hash_key, value)
            return {'status': val}
        else:
            d = self.server.find_node(hash_key, node.address, node.port) # szukamy odpowiedniego serwera, zwracamy deffer
            def callback(res): # res zawiera dane serwera na ktorym moze byc klucz
                # podłączamy się do niego
                d1 = ClientCreator(reactor, amp.AMP).connectTCP(res['address'], res['port'])
                d1.addCallback(lambda p: p.callRemote(commands.Set, key=key, value=value))
                return d1 # deffer, który zawierać będzie wynik metody set na właściwym serwerze
            
            d.addCallback(callback)
            return d
    commands.Set.responder(set)
    
    def find(self, key):
        key = loads(key)
        node = self.node.find_node(key)
        my_key = False
        if node.hash == self.node.start:
            my_key = True
        return {'node' : dumps(node.hash), "address" : node.address, "port" : node.port, 'my_key' : my_key}
    commands.FindNode.responder(find)
    
    def new_node(self, key, address, port):
        key = loads(key)
        node, db, stop = self.node.add_node(key, address, port)
        return {'db' : dumps(db), 'stop' : dumps(stop), 'node' : dumps(node.hash), "address" : node.address, "port" : node.port}
    commands.NewNode.responder(new_node)

    def new_prev(self, node, address, port):
        node = loads(node)
        self.node.new_prev(node, address, port)
        return {'status': True}
    commands.NewPrev.responder(new_prev)

    def reveal(self):
        return {'hash': self.me}
    commands.RevealYourself.responder(reveal)

class ProtoFactory(Factory):
    def __init__(self, me, server, node=None):
        self.me = me
        self.node = node
        self.server = server
    def buildProtocol(self, addr):
        Proto.me = self.me
        return Proto(self.node, self.server)

class Server(object):
    def __init__(self, address, port, next_address=None, next_port=None):
        self.address = address
        self.port = port
        
        self.key = Hash.from_str(address)
        self.pf = ProtoFactory(str(self.key), self)
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
        d.addCallback(lambda p: p.callRemote(commands.FindNode, key=dumps(key)))
        def callback(res):
            res['node'] = loads(res['node'])
            if res['my_key']:
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
            d1.addCallback(lambda p: p.callRemote(commands.NewNode, key=dumps(self.key), address=self.address, port=self.port))
            def new_node(res2):
                # dostajemy jego db, i nastepnika
                self.node = Node(self.address, self.port, 
                self.key, loads(res2['stop']),
                    Neighbor(loads(res2['node']), res2['address'], res2['port']), 
                    Neighbor(res['node'], res['address'], res['port']),
                    loads(res2['db']))
                # dodajemy node do ProtoFactory bo tego mu brakuje
                self.pf.node = self.node
                
                # kontaktujemy się z następnikiem i informujemy, że jesteśmy jego poprzednikiem
                d2 = ClientCreator(reactor, amp.AMP).connectTCP(res2['address'], res2['port'])
                d2.addCallback(lambda p: p.callRemote(commands.NewPrev, node=dumps(self.key), address=self.address, port=self.port))

            d1.addCallback(new_node)

        
        d.addCallback(callback)
        return d

    def run(self):
        print 'nasłuchuje na porcie %d' % args.port
        reactor.listenTCP(self.port, self.pf)
        reactor.run()

if __name__ == '__main__':
    args = parse_server()
    if args.connect:
        args.caddr, args.cport = args.connect.split(':')
        args.cport = int(args.cport)
    else:
        args.caddr = args.cport = None
    server = Server(args.address, args.port, next_address=args.caddr, next_port=args.cport)
    server.run()
