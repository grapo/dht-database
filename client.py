import hashlib

from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator
from twisted.protocols import amp
from args import parse_client
import commands

from twisted.internet import stdio
from twisted.protocols import basic

class CommandProtocol(basic.LineReceiver):
    delimiter = '\n' # unix terminal style newlines. remove this line
                     # for use with Telnet

    def __init__(self, client, *args, **kwargs):
        self.client = client
        # tutaj nie potrzeba super
        
    def connectionMade(self):
        self.sendLine("DHT Klient. Wpisz pomoc aby wyswietlic komendy")

    def lineReceived(self, line):
        # Ignore blank lines
        if not line: return

        # Parse the command
        commandParts = line.split()
        command = commandParts[0].lower()
        args = commandParts[1:]

        # Dispatch the command to the appropriate method.  Note that all you
        # need to do to implement a new command is add another do_* method.
        try:
            method = getattr(self, 'do_' + command)
        except AttributeError, e:
            self.sendLine('Error: no such command.')
        else:
            try:
                method(*args)
            except Exception, e:
                self.sendLine('Error: ' + str(e))

    def do_help(self, command=None):
        """help [command]: List commands, or show help on the given command"""
        if command:
            self.sendLine(getattr(self, 'do_' + command).__doc__)
        else:
            commandss = [cmd[3:] for cmd in dir(self) if cmd.startswith('do_')]
            self.sendLine("Valid commands: " +" ".join(commandss))

    def do_quit(self):
        """quit: Quit this session"""
        self.sendLine('Goodbye.')
        self.transport.loseConnection()
        
    def do_get(self, key):
        key = hashlib.sha1(str(key)).hexdigest()
        self.client.addcall(commands.Get, key=key)
    
    def do_set(self, key, value):
        key = hashlib.sha1(str(key)).hexdigest()
        self.client.addcall(commands.Set, key=key, value=value)

    def __checkSuccess(self, pageData):
        self.sendLine("Success: got %i bytes." % len(pageData))

    def __checkFailure(self, failure):
        self.sendLine("Failure: " + failure.getErrorMessage())

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

    def addcall(self, obj,  **kwargs):
        d = ClientCreator(reactor, amp.AMP).connectTCP(self.address, self.port)
        d.addCallback(lambda p: p.callRemote(obj, **kwargs))
        def callback(res):
            print self
            print "Got result: ", res
        d.addCallback(callback)
        return d


if __name__ == '__main__':
    args = parse_client()
    c = DHTClient(args.address, args.port)
    c.set_interactive()
    c.start()
