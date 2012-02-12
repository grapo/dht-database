#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from ctypes import *

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
			print 'cmp: ', a, b, cmp(a, b)
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
