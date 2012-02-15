#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from ctypes import *
from socket import inet_aton, inet_ntoa

class RouteElement(Structure):
	_filelds_ = [
		("start1", c_uint64),
		("start2", c_uint64),
		("start3", c_uint32),
		("stop1", c_uint64),
		("stop2", c_uint64),
		("stop3", c_uint32),
		("addr", c_uint32),
		]
	
	def __init__(self, start, stop, addr):
		super(RouteElement, self).__init__(
				start1 = (start >> 96) % (1 << 65), 
				start2 = (start >> 32) % (1 << 65), 
				start3 = (start % (1 << 33)),
				stop1 = (stop >> 96) % (1 << 65), 
				stop2 = (stop >> 32) % (1 << 65), 
				stop3 = (stop % (1 << 33)),
				addr = inet_aton(addr))

	def __repr__(self):
		return "(<0x%.8x%.8x%.4x - 0x%.8x%.8x%.4x> at %s)" % (self.start1, self.start2, self.start3, 
			self.stop1, self.stop2, self.stop3, 
			inet_ntoa(self.addr))

	def to_longs(self):
		start = (self.start1 << 96) | (self.start2 << 32) | (self.start3)
		stop = (self.stop1 << 96) | (self.stop2 << 32) | (self.stop3)
		return (start, stop)	

	def __cmp__(self, other):
		(s_start, s_stop) = self.to_longs()
		(o_start, o_stop) = self.to_longs()
		return (cmp(s_stop, o_stop) or cmp(o_start, s_start))

	def between(self, h):
		if (start <= h and h <= stop):
			return 0

class RouteTable(object):
	"""
		Struktura danych zawierajaca adresy poznanych Node sluzaca do szybkiego
	   	wyszukania przyblizonego polozenia klucza

		Korzystamy z funkcji manipulującymy drzewami czerowno-czarnymi z glibc
	"""
	def __init__(self):
		self.libc = CDLL('libc.so.6')
		
		self.CMPFUNC = CFUNCTYPE(c_int, c_char_p, c_char_p)
		def cmp_func(a, b):
			print 'cmp: ', a, b, cmp(a, b),
			return cmp(a, b)
		self.cmp_func = self.CMPFUNC(cmp_func)
		
		self.tsearch = self.libc.tsearch
		self.tsearch.argtypes = [c_char_p, POINTER(c_char_p), self.CMPFUNC]
		self.tsearch.restype = POINTER(c_char_p)
		
		self.tfind = self.libc.tfind
		self.tfind.argtypes = [c_char_p, POINTER(c_char_p), self.CMPFUNC]
		self.tfind.restype = POINTER(c_char_p)
		
		self.tree = c_char_p(None)

	def add(self, s):
		e = c_char_p(str(s))
		print self.tsearch(e, byref(self.tree), self.cmp_func)[0]

		
	def find(self, s):
		e = c_char_p(str(s))
		print self.tfind(e, byref(self.tree), self.cmp_func)[0]

if __name__ == '__main__':
	r = RouteTable()
	r.add("test")
	r.add("test")
	r.add("test2")
	r.find("test")
	ad = RouteElement(0, 500, "192.168.0.1")
	print ad
