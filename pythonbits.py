#!/usr/bin/env python2
# encoding: utf-8
"""
Pythonbits2.py

Created by Ichabond on 2012-07-01.
"""

__version__ = (2, 0)
__version_str__ = '.'.join(str(x) for x in __version__)

import sys
import os
import subprocess
import unicodedata

import ImdbParser
import TvdbParser

from Screenshots import createScreenshots

from ImgurUploader import ImgurUploader

from optparse import OptionParser


def generateSeriesSummary(summary):
    description = "[b]Description[/b] \n"
    if 'seriessummary' in summary:
        description += "[quote]%s\n[spoiler]%s[/spoiler][/quote]\n" % (
            summary['seriessummary'], summary['summary'])
    else:
        description += "[quote]%s[/quote]\n" % summary['summary']
    description += "[b]Information:[/b]\n"
    description += "[quote]TVDB Url: %s\n" % summary['url']
    if 'title' in summary:
        description += "Title: %s\n" % summary['title']
    description += "Show: %s\n" % summary['series']
    if 'aired' in summary:
        description += "Aired: %s\n" % summary['aired']
    if 'rating' in summary:
        description += "Rating: %s\n" % summary['rating']
    if 'genre' in summary:
        description += "Genre: %s\n" % summary['genre']
    if 'director' in summary:
        description += "Director: %s\n" % summary['director']
    if 'writer' in summary:
        description += "Writer(s): %s\n" % summary['writer']
    if 'network' in summary:
        description += "Network: %s\n" % summary['network']
    if 'seasons' in summary:
        description += "Seasons: %s\n" % summary['seasons']
    if 'season' in summary:
        description += "Season: %s\n" % summary['season']
    if 'episode1' in summary:
        description += "Episodes:\n[list=1]\n"
        for i, key in enumerate(summary):
            if i in range(1, summary['episodes'] + 1):
                description += "[*] %s\n" % summary['episode' + str(i)]
        description += "[/list]"
    description += "[/quote]"

    return description


def generateMoviesSummary(summary):
    description = "[b]Description[/b] \n"
    description += "[quote]%s[/quote]\n" % summary['description']
    description += "[b]Information:[/b]\n"
    description += "[quote]IMDB Url: %s\n" % summary['url']
    description += "Title: %s\n" % summary['name']
    description += "Year: %s\n" % summary['year']
    description += "MPAA: %s\n" % summary['mpaa']
    description += "Rating: %s/10\n" % summary['rating']
    description += "Votes: %s\n" % summary['votes']
    description += "Runtime: %s\n" % summary['runtime']
    description += "Director(s): %s\n" % summary['director']
    description += "Writer(s): %s\n" % summary['writers']
    description += "[/quote]"

    return description

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii

def generateTags(summary, num_cast=5):
    cast = [remove_accents(actor
                      ).replace(' ','.'
                      ).replace('-','.'
                      ).replace('\'','.'
                      ).lower() for actor in summary['cast']]
    genres = [g.replace('-','.').lower() for g in summary['genres']]
    return genres+cast[:num_cast]

def findMediaInfo(path):
    mediainfo = None
    try:
        if os.name == "nt":
            mediainfo = subprocess.Popen([r"mediainfo", path], shell=True, stdout=subprocess.PIPE).communicate()[0]
        else:
            mediainfo = subprocess.Popen([r"mediainfo", path], stdout=subprocess.PIPE).communicate()[0]
    except OSError:
        sys.stderr.write(
            "Error: Media Info not installed, refer to http://mediainfo.sourceforge.net/en for installation")
        exit(1)

    return mediainfo


def main(argv):
    usage = 'Usage: %prog [OPTIONS] "MOVIENAME/SERIESNAME" FILENAME'
    parser = OptionParser(usage=usage, version="%%prog %s" % __version_str__)
    parser.add_option("-I", "--info", action="store_true", dest="info",
                      help="Output only info, uses episode or season arguments if available")
    parser.add_option("-e", "--episode", type="string", action="store", dest="episode",
                      help="Provide the TV episode identifier (1x2 or S01E02)")
    parser.add_option("-p", "--season", type="int", action="store", dest="season",
                      help="Provide the season number for season packs")
    parser.add_option("-s", "--screenshots", type="int", action="store", dest="screenshots",
                      help="Set the amount of screenshots, max 7")
    parser.add_option("-S", "--screenshotsonly", type="int", action="store", dest="screenshotsonly",
                      help="Output only screenshots, set the amount of screenshots, max 7")
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
            summary += "Screenshots:\n[quote][align=center]"
            for shot in screenshot:
                summary += "[img=%s]" % shot
            summary += "[/align][/quote]"
            mediainfo = findMediaInfo(filename)
            if mediainfo:
                summary += "[mediainfo]\n%s\n[/mediainfo]" % mediainfo
        print summary
    else:
        imdb = ImdbParser.IMDB()
        imdb.search(search_string)
        imdb.movieSelector()
        summary = imdb.summary()
        movie = generateMoviesSummary(summary)
        tags = generateTags(summary)
        print "\n\n\n"
        print "Year: ", summary['year']
        print "\n\n\n"
        print "Tags: ", ",".join(tags)
        print "\n\n\n"
        print "Movie Description: \n", movie
        print "\n\n\n"
        if not options.info:
            mediainfo = findMediaInfo(filename)
            if mediainfo:
                print "Mediainfo: \n", "[mediainfo]\n",mediainfo,"\n[/mediainfo]"
            for shot in screenshot:
                print "Screenshot: %s" % shot
            cover = ImgurUploader([summary['cover']]).upload()
            if cover:
                print "Image (Optional): ", cover[0]


if __name__ == '__main__':
    main(sys.argv)

