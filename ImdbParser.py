#!/usr/bin/env python
# encoding: utf-8
"""
ImdbParser.py

Created by Ichabond on 2012-07-01.

Module for Pythonbits to provide proper and clean
imdb parsing.

"""

import sys, json

try:
    import imdbpie
except ImportError:
    print >> sys.stderr, "IMDbPie is required for Pythonbits to function"
    sys.exit(1)

class IMDB(object):
    
    def __init__(self):
        self.imdb = imdbpie.Imdb()
        self.results = None
        self.movie = None
        
    def search(self, title):
        try:
            results = self.imdb.find_by_title(title)
        except imdb.IMDbError, e:
            print >> sys.stderr, "You probably don't have an internet connection. Complete error report:"
            print >> sys.stderr, e
            sys.exit(3)

        self.results = results
        
    def movieSelector(self):
        try:
            print "Movies found:"
            for (counter, movie) in enumerate(self.results):
                outp = u'%s: %s (%s)' % (counter, movie['title'], movie['year'])
                print outp
            selection = int(raw_input('Select the correct movie [0-%s]: ' % (len(self.results)-1)))
            self.movie = self.imdb.find_movie_by_id(self.results[selection]['imdb_id'])
            
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
            return {'director' : u" | ".join([director.name for director in self.movie.directors]), 
                    'runtime' : self.movie.runtime, 'rating' : self.movie.rating, 
                    'name' : self.movie.title, 'votes' : self.movie.votes, 'cover' : self.movie.cover_url, 
                    'genre' : u" | ".join([genre for genre in self.movie.genres]), 
                    'writers' : u" | ".join([writer.name for writer in self.movie.writers]), 'mpaa' : self.movie.certification,
                    'description' : self.movie.plot_outline, 
                    'url' : u"http://www.imdb.com/title/%s" % self.movie.imdb_id, 
                    'year' : self.movie.year}
            
if __name__ == "__main__":
    imdb = IMDB()
    imdb.search("Tinker Tailor Soldier Spy")
    imdb.movieSelector()
    summary = imdb.summary()
    print summary