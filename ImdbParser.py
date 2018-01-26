#!/usr/bin/env python
# encoding: utf-8
"""
ImdbParser.py

Created by Ichabond on 2012-07-01.

Module for Pythonbits to provide proper and clean
imdb parsing.

"""

import sys
import json
from attrdict import AttrDict

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
            results = self.imdb.search_for_title(title)
        except imdbpie.ImdbAPIError, e:
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
            selection = int(raw_input('Select the correct movie [0-%s]: ' % (len(self.results) - 1)))
            self.movie = AttrDict(self.imdb.get_title(self.results[selection]['imdb_id']))

        except ValueError as e:
            try:
                selection = int(
                    raw_input("This is not a correct movie-identifier, try again [0-%s]: " % (len(self.results) - 1)))
                self.movie = AttrDict(self.imdb.get_title(self.results[selection]['imdb_id']))
            except (ValueError, IndexError) as e:
                print >> sys.stderr, "You failed"
                print >> sys.stderr, e

        except IndexError as e:
            try:
                selection = int(
                    raw_input("Your chosen value does not match a movie, try again [0-%s]: " % (len(self.results) - 1)))
                self.movie = AttrDict(self.imdb.get_title(self.results[selection]['imdb_id']))
            except (ValueError, IndexError) as e:
                print >> sys.stderr, "You failed"
                print >> sys.stderr, e

    def summary(self):
        if self.movie:
            movie_id = self.movie.base.id.split('/')[2]
            self.movie.credits = self.imdb.get_title_credits(movie_id)['credits']
            self.movie.genres = self.imdb.get_title_genres(movie_id)['genres']
            
            return {'director': u" | ".join([director.name for director in self.movie.credits.director]),
                    'runtime': self.movie.base.runningTimeInMinutes, 'rating': self.movie.ratings.rating,
                    'name': self.movie.base.title, 'votes': self.movie.ratings.ratingCount, 'cover': self.movie.base.image.url,
                    'genre': u" | ".join([genre for genre in self.movie.genres]),
                    'writers': u" | ".join([writer.name for writer in self.movie.credits.writer]),
                    'mpaa': u"N/A",
                    'description': self.movie.plot.outline.text,
                    'url': u"http://www.imdb.com/title/%s" % movie_id,
                    'year': self.movie.base.year}


if __name__ == "__main__":
    imdb = IMDB()
    imdb.search("Tinker Tailor Soldier Spy")
    imdb.movieSelector()
    summary = imdb.summary()
    print summary
