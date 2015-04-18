#!/usr/bin/env python
# encoding: utf-8
"""
TvdbUnitTests.py

Created by Ichabond on 2012-07-03.
"""

import unittest
from TvdbParser import TVDB


class TvdbTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.tvdb = TVDB()
        self.Episode = self.tvdb.search("Burn Notice", episode="S06E01")
        self.Season = self.tvdb.search("Burn Notice", season=6)
        self.Show = self.tvdb.search("Scrubs")

    def testEpisode(self):
        self.assertEqual(self.Episode["episodename"], "Scorched Earth")
        self.assertEqual(self.Episode["director"], "Stephen Surjik")
        self.assertEqual(self.Episode['firstaired'], "2012-06-14")
        self.assertEqual(self.Episode['writer'], "Matt Nix")
        self.assertEqual(len(self.Episode), 26)


    def testSeason(self):
        self.assertEqual(len(self.Season), 10)

    def testShow(self):
        self.assertEqual(len(self.Show.data), 25)
        self.assertEqual(len(self.Show), 10)
        self.assertEqual(self.Show['network'], "ABC")
        self.assertEqual(self.Show['seriesname'], "Scrubs")

    def testSummaries(self):
        self.tvdb.search("Burn Notice", episode="S06E01")
        BurnNoticeS06E01 = {'director': u'Stephen Surjik', 'rating': u'7.9',
                            'aired': u'2012-06-14', 'language': u'en',
                            'title': u'Scorched Earth', 'genre': u'|Action and Adventure|',
                            'summary': u'Michael pursues Anson in Miami. Meanwhile, Fiona is taken into custody and interrogated by a former foe.',
                            'writer': u'Matt Nix',
                            'url': u'http://thetvdb.com/?tab=episode&seriesid=80270&seasonid=483302&id=4246443',
                            'series': u'Burn Notice'}
        self.assertEqual(self.tvdb.summary(), BurnNoticeS06E01)
        self.tvdb.search("Burn Notice", season=5)
        BurnNoticeS05 = {'episode11': u'Better Halves', 'episode17': u'Acceptable Loss',
                         'episode15': u'Necessary Evil', 'episode12': u'Dead to Rights',
                         'episode13': u'Damned If You Do', 'episode3': u'Mind Games',
                         'episode1': u'Company Man', 'episode10': u'Army of One', 'episodes': 18,
                         'episode2': u'Bloodlines', 'episode5': u'Square One', 'episode4': u'No Good Deed',
                         'episode7': u'Besieged', 'episode6': u'Enemy of My Enemy',
                         'episode9': u'Eye for an Eye', 'episode8': u'Hard Out', 'episode18': u'Fail Safe',
                         'episode16': u'Depth Perception', 'episode14': u'Breaking Point',
                         'url': u'http://thetvdb.com/?tab=season&seriesid=80270&seasonid=463361',
                         'series': u'Burn Notice',
                         'summary': u'Covert intelligence operative Michael Westen has been punched, kicked, choked and shot. And now he\'s received a "burn notice", blacklisting him from the intelligence community and compromising his very identity. He must track down a faceless nemesis without getting himself killed while doubling as a private investigator on the dangerous streets of Miami in order to survive.'}
        self.assertEqual(self.tvdb.summary(), BurnNoticeS05)
        self.tvdb.search("Scrubs")
        Scrubs = {'rating': u'9.0', 'network': u'ABC', 'series': u'Scrubs', 'contentrating': u'TV-PG',
                  'summary': u'Scrubs focuses on the lives of several people working at Sacred Heart, a teaching hospital. It features fast-paced dialogue, slapstick, and surreal vignettes presented mostly as the daydreams of the central character, Dr. John Michael "J.D." Dorian.',
                  'seasons': 10, 'url': u'http://thetvdb.com/?tab=series&id=76156'}
        self.assertEqual(self.tvdb.summary(), Scrubs)
