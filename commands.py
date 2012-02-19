from twisted.protocols import amp
from node import KeyNotHere

class Get(amp.Command):
    arguments = [('key', amp.String())]
    response = [('value', amp.String())]
    errors = {KeyNotHere: 'KEY_NOT_HERE'}

class Set(amp.Command):
    arguments = [('key', amp.String()),
                 ('value', amp.String())]
    response = [('status', amp.Boolean())]

class FindNode(amp.Command):
    arguments = [('key', amp.String())]
    response = [('node', amp.String()), ('address', amp.String()), ('port', amp.Integer()), ('my_key', amp.Boolean()) ]

class NewNode(amp.Command):
    arguments = [('key', amp.String()), ('address', amp.String()), ('port', amp.Integer())]
    response = [('db', amp.String()),('stop', amp.String()), 
                ('node', amp.String()), ('address', amp.String()),
                ('port', amp.Integer())]

class NewPrev(amp.Command):
    arguments = [('node', amp.String()), ('address', amp.String()),
                ('port', amp.Integer())]
    response = [('status', amp.Boolean())]

class RevealYourself(amp.Command):
    arguments = []
    response = [('hash', amp.String())]
