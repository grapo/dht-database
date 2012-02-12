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
