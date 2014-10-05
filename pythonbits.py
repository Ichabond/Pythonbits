#!/usr/bin/env python
# encoding: utf-8
"""
Pythonbits2.py

Created by Ichabond on 2012-07-01.
"""

__version__ = (2, 0)
__version_str__ = '.'.join(str(x) for x in __version__)

import sys, os, subprocess

import ImdbParser, TvdbParser

from Screenshots import createScreenshots

from ImageUploader import Upload

from optparse import OptionParser

def generateSeriesSummary(summary):
	
	description = "[b]Description[/b] \n"
	if 'seriessummary' in summary:
		description = description + "[quote]%s\n[spoiler]%s[/spoiler][/quote]\n" % (summary['seriessummary'], summary['summary'])
	else:
		description = description + "[quote]%s[/quote]\n" % summary['summary']
	description = description + "[b]Information:[/b]\n"
	description = description +"[quote]TVDB Url: %s\n" % summary['url']
	if 'title' in summary:
		description = description + "Title %s\n" % summary['title']
	description = description + "Show: %s\n" % summary['series']
	if 'aired' in summary:
		description = description + "Aired: %s\n" % summary['aired']
	if 'rating' in summary:
		description = description + "Rating: %s\n" % summary['rating']
	if 'genre' in summary:
		description = description + "Genre: %s\n" % summary['genre']
	if 'director' in summary:
		description = description + "Director: %s\n" % summary['director']
	if 'writer' in summary:
		description = description + "Writer(s): %s\n" % summary['writer']
	if 'network' in summary:
		description = description + "Network: %s\n" % summary['network']
	if 'seasons' in summary:
		description = description + "Seasons: %s\n" % summary['seasons']
	if 'season' in summary:
		description = description + "Season: %s\n" % summary['season']
	if 'episode1' in summary:
		description = description + "Episodes:\n[list=1]\n"
		for i, key in enumerate(summary):
        	if i in range (1,summary['episodes']+1):
                description = description + "[*] %s\n" % summary['episode'+str(i)]
		description = description + "[/list]"
	description = description + "[/quote]"
	
	return description
	
def generateMoviesSummary(summary):

	description = "[b]Description[/b] \n"
	description = description + "[quote]%s[/quote]\n" % summary['description']
	description = description + "[b]Information:[/b]\n"
	description = description +"[quote]IMDB Url: %s\n" % summary['url']
	description = description + "Title: %s\n" % summary['name']
	description = description + "Year: %s\n" % summary['year']
	description = description + "MPAA: %s\n" % summary['mpaa']
	description = description + "Rating: %s/10\n" % summary['rating']
	description = description + "Votes: %s\n" % summary['votes']
	description = description + "Runtime: %s\n" %summary['runtime']
	description = description + "Director(s): %s\n" % summary['director']
	description = description + "Writer(s): %s\n" % summary['writers']
	description = description + "[/quote]"
		
	return description
	
def findMediaInfo(path):
	mediainfo = None
	try:
		if os.name=="nt":
			mediainfo = subprocess.Popen([r"mediainfo",path], shell=True, stdout=subprocess.PIPE).communicate()[0]
		else:
			mediainfo = subprocess.Popen([r"mediainfo",path], stdout=subprocess.PIPE).communicate()[0]
	except OSError:
		sys.stderr.write("Error: Media Info not installed, refer to http://mediainfo.sourceforge.net/en for installation")
		exit(1)
	
	return mediainfo

def main(argv):
	usage = 'Usage: %prog [OPTIONS] "MOVIENAME/SERIESNAME" FILENAME'
	parser = OptionParser(usage=usage, version="%%prog %s" % __version_str__)
	parser.add_option("-I", "--info", action="store_true", dest="info",
		help="Output only info, uses episode or season arguments if available")
	parser.add_option("-e", "--episode", type="string", action="store", dest="episode",
		help="Provide the TV episode identifier (1x2 or S01E02)")
	parser.add_option("-p", "--season", type="int", action="store", dest="season", help="Provide the season number for season packs")
	parser.add_option("-s", "--screenshots", type="int", action="store", dest="screenshots", help="Set the amount of screenshots, max 7")
	parser.add_option("-S", "--screenshotsonly", type="int", action="store", dest="screenshotsonly", help="Output only screenshots, set the amount of screenshots, max 7")
	options, args = parser.parse_args()
	if len(args) == 0:
		parser.print_help()
		sys.exit(1)
	if options.screenshotsonly:
		filename = args[0]
		screenshot = createScreenshots(filename, shots=options.screenshotsonly)
	else:
		search_string = args[0]
		if not options.info:
			filename = args[1]
			if options.screenshots:
				screenshot = createScreenshots(filename, shots=options.screenshots)
			else:
				screenshot = createScreenshots(filename)
	if options.screenshotsonly:
		for shot in screenshot:
			print shot
	elif options.season or options.episode:
		tvdb = TvdbParser.TVDB()
		if options.season:
			tvdb.search(search_string, season=options.season)
		if options.episode:
			tvdb.search(search_string, episode=options.episode)
		summary = tvdb.summary()
		summary = generateSeriesSummary(summary)
		if not options.info:
			summary = summary + "Screenshots:\n[quote][align=center]"
			for shot in screenshot:
				summary = summary + "[img=%s]" % shot
			summary = summary + "[/align][/quote]"
			mediainfo = findMediaInfo(filename)
			if mediainfo:
				summary = summary + "[mediainfo]\n%s\n[/mediainfo]" % mediainfo
		print summary
	else:
		imdb = ImdbParser.IMDB()
		imdb.search(search_string)
		imdb.movieSelector()
		summary = imdb.summary()
		movie = generateMoviesSummary(summary)
		print "\n\n\n"
		print "Year: ", summary['year']
		print "\n\n\n"
		print "Movie Description: \n", movie
		print "\n\n\n"
		if not options.info:
			mediainfo = findMediaInfo(filename)
			if mediainfo:
				print "Mediainfo: \n", mediainfo
			for shot in screenshot:
				print "Screenshot: %s" % shot
			cover = Upload([summary['cover']]).upload()
			if cover:
				print "Image (Optional): ", cover[0]
			
		
		

if __name__ == '__main__':
	
	main(sys.argv)

