#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import hashlib

from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator
from twisted.protocols import amp
from twisted.internet import stdio
from twisted.protocols import basic


from args import parse_client
import commands


class CommandProtocol(basic.LineReceiver):
    delimiter = '\n' 

    def __init__(self, client, *args, **kwargs):
        self.client = client
        # tutaj nie potrzeba super
        
    def connectionMade(self):
        self.sendLine("DHT Klient. Wpisz pomoc aby wyświetlić komendy")

    def lineReceived(self, line):
        if not line: return

        # Parse the command
        commandParts = line.split()
        command = commandParts[0].lower()
        args = commandParts[1:]

        # Obsługuje komendę za pomocą odpowiedniej metody.
        # Aby dodać nową komendę i metodę ją obsługującą należy tylko
        # dodać metodę do_* do klasy.
        try:
            method = getattr(self, 'do_' + command)
        except AttributeError, e:
            self.sendLine('Błąd: nie ma takiej komendy.')
        else:
            try:
                method(*args)
            except Exception, e:
                self.sendLine('Błąd: ' + str(e))

    def do_help(self, command=None):
        """help [command]: Wypisuje komendy lub wyświetla pomoc do określonej komendy"""
        if command:
            self.sendLine(getattr(self, 'do_' + command).__doc__)
        else:
            commandss = [cmd[3:] for cmd in dir(self) if cmd.startswith('do_')]
            self.sendLine("Poprawne komendy: " +" ".join(commandss))

    def do_quit(self):
        """quit: Zamyka program"""
        self.sendLine('Do widzenia.')
        self.transport.loseConnection()
        
    def do_get(self, key):
        """get [klucz]: Zwraca wartość zachowaną pod danym kluczem"""
        key = hashlib.sha1(str(key)).hexdigest()
        def callback(res):
            self.sendLine("Otrzymano: {0}".format(res['value']))
        self.client.addcall(commands.Get, callback=callback, key=key)
    
    def do_set(self, key, value):
        """set [klucz] [wartość]: Zapisuje wartość pod danym kluczem"""
        key = hashlib.sha1(str(key)).hexdigest()
        def callback(res):
            if res['status']:
                self.sendLine("Zapisano wartość")
        self.client.addcall(commands.Set, callback=callback, key=key, value=value)

    def __checkFailure(self, failure):
        self.sendLine("Błąd: " + failure.getErrorMessage())

    def connectionLost(self, reason):
        # stop the reactor, only because this is meant to be run in Stdio.
        reactor.stop()

class DHTClient(object):
    def __init__(self, address, port):
        self.address = address
        self.port = port

    def set_interactive(self):
        stdio.StandardIO(CommandProtocol(self))

    def start(self):
        reactor.run()

    def addcall(self, obj, callback=None, **kwargs):
        d = ClientCreator(reactor, amp.AMP).connectTCP(self.address, self.port)
        d.addCallback(lambda p: p.callRemote(obj, **kwargs))
        if callback is None:
            def callback(res):
                print "Otrzymano: ", res
        d.addCallback(callback)
        def trapError(result):
            result.trap(Exception)
            print "Błąd!: {0}".format(result.type)
        d.addErrback(trapError)
        return d


if __name__ == '__main__':
    args = parse_client()
    c = DHTClient(args.address, args.port)
    c.set_interactive()
    c.start()
