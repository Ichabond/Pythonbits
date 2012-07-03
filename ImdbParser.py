#!/usr/bin/env python
# encoding: utf-8
"""
ImdbParser.py

Created by Ichabond on 2012-07-01.

Module for Pythonbits to provide proper and clean
imdb parsing.

"""

import sys

try:
	import imdb
except ImportError:
	print >> sys.stderr, "IMDbPY is required for Pythonbits to function"
	sys.exit(1)

class IMDB(object):
	
	def __init__(self):
		self.imdb = imdb.IMDb(adultSearch=0)
		self.results = None
		self.movie = None
		
	def search(self, title):
		try:
			results = self.imdb.search_movie(title)
		except imdb.IMDbError, e:
			print >> sys.stderr, "You probably don't have an internet connection. Complete error report:"
			print >> sys.stderr, e
			sys.exit(3)
			
		self.results = results
		
	def movieSelector(self):
		try:
			print "Movies found:"
			for (counter, movie) in enumerate(self.results):
				outp = u'%s: %s' % (counter, movie['long imdb title'])
				print outp
			selection = int(raw_input('Select the correct movie [0-%s]: ' % (len(self.results)-1)))
			self.movie = self.imdb.get_movie(self.imdb.get_imdbID(self.results[selection]))
			
		except ValueError as e:
			try:
				selection = int(raw_input("This is not a correct movie-identifier, try again [0-%s]: " % (len(self.results)-1)))
				self.movie = self.imdb.get_movie(self.imdb.get_imdbID(self.results[selection]))
			except (ValueError, IndexError) as e:
				print >> sys.stderr, "You failed"
				print >> sys.stderr, e
				
		except IndexError as e:
			try:
				selection = int(raw_input("Your chosen value does not match a movie, try again [0-%s]: " % (len(self.results)-1)))
				self.movie = self.imdb.get_movie(self.imdb.get_imdbID(self.results[selection]))
			except (ValueError, IndexError) as e:
				print >> sys.stderr, "You failed"
				print >> sys.stderr, e
				
	def summary(self):
		if self.movie:
			return {'director' : u" | ".join([director['long imdb name'] for director in self.movie['director']]), 
					'runtime' : u" | ".join([runtime for runtime in self.movie['runtime']]), 'rating' : self.movie['rating'], 
					'name' : self.movie['long imdb title'], 'languages' : u" | ".join([language for language in self.movie['languages']]),
					'votes' : self.movie['votes'], 'cover' : self.movie['full-size cover url'], 
					'genre' : u" | ".join([genre for genre in self.movie['genres']]), 
					'writers' : u" | ".join([writer['long imdb name'] for writer in self.movie['writer']]), 'mpaa' : self.movie['mpaa'],
					'description' : self.movie['plot outline'], 
					'music' : u" | ".join([composer['long imdb name'] for composer in self.movie['original music']]),
					'url' : u"http://www.imdb.com/title/tt%s" % self.imdb.get_imdbID(self.movie), 
					'year' : self.movie['year']}
			
if __name__ == "__main__":
	imdb = IMDB()
	imdb.search("Tinker Tailor Soldier Spy")
	imdb.movieSelector()
	summary = imdb.summary()
	print summary