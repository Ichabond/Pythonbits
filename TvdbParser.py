#!/usr/bin/env python
# encoding: utf-8
"""
TvdbParser.py

Created by Ichabond on 2012-07-01.
"""

from inspect import getmembers

import re, sys
try:
	import tvdb_api
except ImportError:
	print >> sys.stderr, "tvdb_api is required for Pythonbits to function"
	sys.exit(1)

class TVDB(object):
	
	def __init__(self):
		self.tvdb = tvdb_api.Tvdb()
		self.episode = None
		self.season = None
		self.show = None
		
	def search(self, series, season=None, episode=None,):
		if episode:
			matchers = [ re.compile(r'(\d+)x(\d+)'), re.compile(r'(?i)s(\d+)e(\d+)')]
			tv_episode = None
			for matcher in matchers:
				ma = matcher.match(episode)
				if ma:
					tv_episode = (int(ma.group(1)), int(ma.group(2)))
					break
					
			if not tv_episode:
				print >> sys.stderr, "Unable to decipher your tv-episode \"%s\"" % episode
				sys.exit(1)
			
			self.episode = self.tvdb[series][tv_episode[0]][tv_episode[1]]
			self.season = None
			self.show = self.tvdb[series]
			return self.episode
		if isinstance(season, int):
			self.season = self.tvdb[series][season]
			self.episode = None
			self.show = self.tvdb[series]
			return self.season
			
		else:
			self.show = self.tvdb[series]
			self.season = None
			self.episode = None
			return self.show
			
	def summary(self):
		if isinstance(self.episode, tvdb_api.Episode) and not self.season:
			return {'title' : self.episode['episodename'], 'director' : self.episode['director'], 'aired' : self.episode['firstaired'], 
					'writer' : self.episode['writer'], 'rating' : self.episode['rating'], 'summary' : self.episode['overview'],
					'language' : self.episode['language'], 'genre' : self.tvdb[int(self.episode['seriesid'])]['genre'], 
					'url' : "http://thetvdb.com/?tab=episode&seriesid="+self.episode['seriesid']+"&seasonid="+self.episode['seasonid']+"&id="+self.episode['id'],
					'series' : self.show['seriesname'], 'seriessummary' : self.show['overview']}
		elif isinstance(self.season, tvdb_api.Season):
			summary = {'episodes' : len(self.season), 'series' : self.show['seriesname']}
			for (counter, episode) in enumerate(self.season):
				summary['url'] = "http://thetvdb.com/?tab=season&seriesid="+self.season[episode]['seriesid']+"&seasonid="+self.season[episode]['seasonid']
				summary["episode"+str(counter+1)] = self.season[episode]['episodename']
			summary['summary'] = self.show['overview']
			return summary
		if isinstance(self.show, tvdb_api.Show):
			return {'series' : self.show['seriesname'], 'seasons' : len(self.show), 'network' : self.show['network'], 
					'rating' : self.show['rating'], 'contentrating' : self.show['contentrating'], 'summary' : self.show['overview'],
					'url' : "http://thetvdb.com/?tab=series&id="+self.show['id']}
