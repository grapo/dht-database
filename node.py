#!/usr/bin/env python2
# -*- coding: utf-8 -*-


# Szybki projekt rozproszonej bazy danych

# Używamy hashy 160 bitowych przechowywanych jako hex, następnikiem
# ostatniego jest pierwszy hash.
# 
# Na początku w sieci działa 1 węzeł (Node) obsługujący wszysktie
# hashe od nodeid do nodeid-1.
# 
# Każdy węzeł posiada id który jest hashem adresu MAC. Gwarantuje to, 
# że po odłączeniu i ponownym dołączeniu węzeł przejmi te same wpisy.
#
# Jeśli do sieci dołącza n-ty węzeł o id <nid> to pyta on jednego
# z obecnych o węzeł na którym leży klucz nid. Nastepnie kontaktuje 
# on się z tą węzłem i przejmuje od nigo klucze od nid do końca
# posiadanego przez niego zakresu. Węzeł nid zostaje jego
# następnikiem
# 
# Jeśli węzeł nid odłącza się od sieci to kontaktuje się ze swoim 
# poprzednikiem, przekazuje mu swoje klucze i podaje mu swojego
# nastepnika
#
# Szukanie klucza:
# Klient kontaktuje się z dowolnym węzłem i podaj mu szukany klucz.
# Węzeł na podstawie swojej tablicy skrótów próbuje podać najlepszą
# znaną lokalizację klucza. Jeśli się to nie uda podaje następnika.
# Wskazaną maszynę odpytujemy o klucz.
# W przechodzeniiu po komputerach można by użyć dwóch strategii:
# 1. Klient łączy się z dowolnym węzłem i dostaje adres węzła na którym
# będzie klucz - to znaczy że węzły bedą musiały łączyć się po kolei
# między sobą.
# 2. Klient łączy się z węzłem i dostaje węzeł znajdujący się bliżej
# klucza - wtesy odpadają połączenia między węzłami - po prostu
# zwracamy węzeł który wydaje się nam lepszy, za to klient będzie 
# miał więcej roboty.
# Ew. można to pomieszać - węzeł z którym łączy się klient staje się
# nowym klientem i realizuje strategię 2. 
#
# Cechy systemów rozproszonych jakie realizuje nasz system:
# 
# Dzielenie zasobów - wielu użytkowników może korzystać równocześnie
# 
# Otwartość - możliwość rozbudowy 
# 
# Współbieżność - no jest :)
# 
# Skalowalność - łatwo dodawać kolejne węzły. Przy dobrze wykonanej
# tablicy skrótów. Czas dostępu będzie O(logn)
# 
# Przeźroczystość - zależy jak się zdefiniuje. Przy strategii szukania
# klucza 1 lub mieszanej klient nie będzie wiedział że ma do czynienia 
# z systemem rozproszonym. Przy 2 można powiedzieć, że chociaż klient wie
# to użytkownik nie więc jest to na innej warstwie ulokowane.
#
# Nie mamy tolerowania awarii
#

import hashlib

class RouteTable(object):
    """Struktura danych zawierajaca adresy poznanych Node sluzaca do szybkiego
       wyszukania przyblizonego polozenia klucza
    """
    pass

class MyDict(dict):
    """Naiwna implementacja dzielonej tablicy hashującej"""
    def getall(self, start, stop):
        return MyDict(filter(lambda (k, _): k.beetwen(start, stop), self.viewitems()))

    def __missing__(self, key):
        raise KeyNotHere()


class Hash(object):
    """
        Klucz w tablicy hashującej. Na kluczach zdefiniowany jest porządek
        leksykograficzny. ("0" < "a" < "b"; "0a" < "0b")
    
    """
    # obecna implementacja działa dla kluczy hashowanych sha1 (160 bitów)
    length = 40
    start = long(0)
    stop = long(2^161-1)
    max = long(2^161-1)

    def __init__(self, hs):
        self.hash = hs
    
    @classmethod
    def from_hex(cls, h):
        if len(h) == cls.length:
            return cls(long(h, 16))
        else:
            raise TypeError

    @classmethod
    def from_str(cls, s):
        return cls.from_hex(hashlib.sha1(str(s)).hexdigest())

    def prev(self):
        """ Poprzedni hash"""
        if self.hash == 0:
            return Hash(self.max)
        else:
            return Hash(self.hash - 1)

    def next(self):
        """ Następny hash"""
        if self.hash == max:
            return Hash(long(0))
        else:
            return Hash(self.hash + 1)

    def beetwen(self, start, stop):
        """ Czy hash znajduje się pomiędzy hashami start i stop """
        if start > stop :
            return start <= self or self <= stop 
        else:
            return start <= self <= stop

    def __ge__(self, other):
        return self.hash >= other.hash
    
    def __le__(self, other):
        return self.hash <= other.hash
    
    def __gt__(self, other):
        return self.hash > other.hash
    
    def __lt__(self, other):
        return self.hash < other.hash

    def __repr__(self):
        return "0x%.40x" % self.hash

    def __hash__(self):
        return self.hash

    def __cmp__(self, other):
        return self.__gt__(other) - self.__lt__(other)

    def __eq__(self, other):
        return self.hash == other.hash

    
class Neighbor(object):
    def __init__(self, hash, address, port):
        assert isinstance(hash, Hash)
        self.hash = hash
        self.address = address
        self.port = port
    
    def unpack(self):
        return (self.hash, self.address, self.port)


class KeyNotHere(Exception):
    pass 


class Node(object):
    def __init__(self, address, port, start, stop, next=None, prev=None, db=MyDict()):
        assert isinstance(start, Hash)
        assert isinstance(stop, Hash)
        self.start = start # start to takze adres maszyny
        self.stop = stop
        self.db = db
        self.im = Neighbor(start, address, port)
        
        if next:
            self.next = next
        else:
            self.next = self.im
        
        if prev:    
            self.prev = prev
        else:
            self.next = self.im

        #self.route_table = RouteTable([next, prev])

    def set(self, key, value):
        assert isinstance(key, Hash)
        if key.beetwen(self.start, self.stop):
            self.db[key] = value
            return True
        else:
            return False
        
    
    def find(self, key):
        """ Zwraca wartość pod danym kluczem """
        assert isinstance(key, Hash)
        if key.beetwen(self.start, self.stop):
            return self.db[key]
        else:
            raise KeyNotHere()
    
    def find_node(self, key):
        """ Zwraca węzeł na którym znajduję się dany klucz """
        assert isinstance(key, Hash)
        if key.beetwen(self.start, self.stop):
            return self.im
        else:
            return self.next

    def add_node(self, key, address, port):
        """ 
            Dodaje nowy węzeł-syn do danego węzła i kopiuje
            do niego część kluczy
        """
        assert isinstance(key, Hash)
        if key.beetwen(self.start, self.stop):
            n = Neighbor(key, address, port)
            old_next = self.next
            self.next = n
            new_db = self.db.getall(key, self.stop)
            old_stop = self.stop
            self.stop = key.prev()
            return old_next, new_db, old_stop 

    def new_prev(self, node, address, port):
        """ Przełącza się na nowego poprzednika """
        self.prev = Neighbor(node, address, port)

    def __repr__(self):
        return "<{0}>  P : {1} N : {2}".format(self.start, self.prev.start, self.next.start)



if __name__ == '__main__':
    import random
    from args import parse_client

    args = parse_client()
    h = Hash.from_str(random.random())
    n = Node(args.address, args.port, h, h.prev())
    k1 = Hash.from_str(random.random())
    k2 = k1.next()
    k3 = k2.next()
    print "Adding key: ", n.set(k1, "Key 1")
    print "Adding key: ", n.set(k2, "Key 2")
    print "Adding key: ", n.set(k3, "Key 3")
    print "Finding key: ", n.find(k2)
    print "Finding key's node: ", n.find_node(k2)
    print "Getting database: ", n.add_node(k2, args.address, args.port)
