#!/usr/bin/env python
# vim:noexpandtab:
# coding =<iso-8859-15>
#       Copyright (c) 2010, scootypuffjr
#       Copyright (c) 2010, Apollo
#       All rights reserved.
#
#       Redistribution and use in source and binary forms, with or without
#       modification, are permitted provided that the following conditions are met:
#               * Redistributions of source code must retain the above copyright
#                 notice, this list of conditions and the following disclaimer.
#               * Redistributions in binary form must reproduce the above copyright
#                 notice, this list of conditions and the following disclaimer in the
#                 documentation and/or other materials provided with the distribution.
#               * Neither the name of the organization nor the
#                 names of its contributors may be used to endorse or promote products
#                 derived from this software without specific prior written permission.
#
#       THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#       ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#       WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#       DISCLAIMED. IN NO EVENT SHALL SCOOTYPUFFJR BE LIABLE FOR ANY
#       DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#       (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#       LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#       ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#       (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#       SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Python module to retrieve information from imdb.com and Media Info for baconbits"""

__version__ = (0, 2)
__version_str__ = '.'.join(str(x) for x in __version__)
__author__ = "Apollo"

import urllib
import urllib2
import urlparse
import sys
import re
import subprocess
import tempfile
import microdata
import os
import json
import MultipartPostHandler
from xml.dom.minidom import Document, parse

__htmlparser = True
try:
	from HTMLParser import HTMLParser
except:
	__htmlparser = False

def __logerror(msg):
	sys.stderr.write(msg)

if __htmlparser:
	__converter = HTMLParser()

def tempdir():
	return tempfile.gettempdir()+os.sep

def decode(text):

	"""Takes a string and replaces any html entities it contains with their unicode
	counterparts.
	"""

	if __htmlparser:
	## HACK, HTMLParser() sucks @ utf-8
		return __converter.unescape(text.decode('utf-8')).encode('utf-8')
	else:
		charrefpat = re.compile(r'&(#(\d+|x[\da-fA-F]+)|[\w.:-]+);?')
		from htmlentitydefs import name2codepoint
		if type(text) is unicode:
			uchr = unichr
		else:
			uchr = lambda value: value > 255 and unichr(value) or chr(value)

		def entitydecode(match, uchr=uchr):
			entity = match.group(1)
			if entity.startswith('#x'):
				return uchr(int(entity[2:], 16))
			elif entity.startswith('#'):
				return uchr(int(entity[1:]))
			elif entity in name2codepoint:
				return uchr(name2codepoint[entity])
			else:
				return match.group(0)
		return charrefpat.sub(entitydecode, text)

class FetchError(Exception):
	def __init__(self, value):
		self.parameter = value
	def __str__(self):
		return repr(self.parameter)

class URLError(Exception):
	def __init__(self, value):
		self.parameter = value
	def __str__(self):
		return repr(self.parameter)

class Error404(Exception):
	def __init__(self, value):
		self.parameter = value
	def __str__(self):
		return repr(self.parameter)

class _MyOpener(urllib.FancyURLopener):
	version = 'Opera/9.80 (fX11; Linux i686; U; en) Presto/2.2.15 Version/10.00'
	def __init__(self, *args, **kwargs):
		urllib.FancyURLopener.__init__(self, *args, **kwargs)
		# force the results into English even if the GeoIP says otherwise
		self.addheader('Accept-Language','en-us, en')

class PythonbitsConfig:
	"""Class for holding pythonbits config strings. read() or create_dom() must be called before first use. Access strings through obj.strings[key]"""
	def __init__(self):
		self.strings={}
		self.file=tempdir()+"config.xml"
		if not os.path.exists(self.file):
			update_url = "https://github.com/Ichabond/Pythonbits/raw/master/config.xml"
			opener = _MyOpener()
			nconf = opener.open(update_url)
			if nconf.info()["Status"]=="200 OK":
				fh = open(tempdir()+"config.xml", "w")
				fh.write(nconf.read())
				fh.close()
			else:
				__logerror("Cannot update config file.")
			nconf.close()


	def __del__(self):
		self.file.close()

	def read(self, file=0):
		if file==0:
			file=self.file
		self.xml = parse(file)
		self.load_strings()

	def write(self, file=0):
		if file==0:
			file=self.file
		location = self.file.name
		file.close()
		file = open(location, "w")
		file.write(self.xml.toprettyxml())
		file.close()
		self.file = open(location, "r")

	def set_location(self, location):
		try:
			self.file = open(location, "r")
		except IOError:
			self.file = open(location, "w")

	def load_strings(self):
		for node in self.xml.getElementsByTagName("string"):
			self.strings[node.getAttribute("name")]=node.firstChild.data.replace('\n','').replace('\t','')

	def add_string(self, name, data):
		container = self.xml.getElementsByTagName("pythonbits")[0]
		stringtag = self.xml.createElement("string")
		stringtag.setAttribute("name", name)
		stringtag.appendChild(self.xml.createTextNode(data))
		container.appendChild(stringtag)
		self.load_strings()
	def del_string(self, name):
		del self.strings[name]
		###Horrible hack. Write real code.
		self.create_dom()
		for (name, entry) in self.strings.items():
			self.add_string(name, entry)
	def create_dom(self):
		self.xml = Document()
		self.xml.appendChild(self.xml.createElement("pythonbits"))

class SearchTV(object):
	"""Searches for the specified show name with a given season,show tuple.
	"""
	def __init__(self, searchString, episode_tuple):
		"""
		Searches for the provided show name and the given episode information.
		:param searchString: the show name to search for
		:param episode_tuple: the (season, show-number) tuple of that show
		"""
		try:
			template = conf.strings['tvrage_quickinfo'].strip()
		except KeyError, ke:
			print >> sys.stderr, "Unable to look up the quickinfo template", ke
			print >> sys.stderr, "Keys: ", conf.strings.keys()
			print >> sys.stderr, "XML location", tempdir()
			raise
		# no matter how they presented it, we want it in SxE format
		episode_cross = '%sx%s' % episode_tuple
		quoted_search = urllib.quote( searchString )
		search_url = template % {'query':quoted_search,'episode_cross':episode_cross}
		# print "SearchURL=", search_url
		opener = _MyOpener()
		fh = opener.open( search_url )
		info = fh.read()
		# they return a leading <pre> as part of their "API"; great
		info = re.sub(r'^\s*<pre>', '', info)
		# print "Info <<<",info,">>>"
		fh.close()
		self.result = self._parse_tvrage_quickinfo( info )

	def _parse_tvrage_quickinfo(self, info ):
		"""
		As per the documentation found at <http://www.tvrage.com/info/quickinfo.html>


		[An Example]
Show ID@27924
Show Name@The Franchise: A Season with the San Francisco Giants
Show URL@http://www.tvrage.com/The_Franchise-A_Season_with_the_San_Fran
Premiered@2011
Started@Apr/13/2011
Ended@
Episode Info@01x03^Season 1, Episode 3^27/Jul/2011
Episode URL@http://www.tvrage.com/The_Franchise-A_Season_with_the_San_Fran/episodes/1065050931
Latest Episode@01x06^Season 1, Episode 6^Aug/17/2011
Next Episode@01x07^Season 1, Episode 7^Aug/24/2011
RFC3339@2011-08-24T22:00:00-4:00
GMT+0 NODST@1314230400
Country@USA
Status@New Series
Classification@Reality
Genres@Action | Celebrities | Family | Fitness | Lifestyle | Sports | Talent
Network@Showtime
Airtime@Wednesday at 10:00 pm
Runtime@30
		"""
		results = {}
		# these are fields which are further subdelimited by "^" markers
		special_fields = ['Episode Info', 'Latest Episode', 'Next Episode']
		special_subfields = {
			'Episode Info':['Episode Tuple','Episode Description','Air Date'],
			'Latest Episode':[
				'Latest Episode Tuple','Latest Episode Description','Latest Air Date'],
			'Next Episode':[
				'Next Episode Tuple','Next Episode Description','Next Air Date']
		}
		# these are fields which contain mmm/dd/yyyy formatted dates
		date_fields = ['Started', 'Ended']
		lines = re.split(r'[\r\n]', info)
		for line in lines:
			if not len(line):
				continue
			key_value = re.split(r'@', line)
			kv_len = len(key_value)
			if 2 != kv_len:
				raise ValueError("Expected 2 fields but found %d in %s" \
						% (kv_len, line))
			( field_name, value ) = key_value
			if field_name in special_fields and len(value) > 0:
				values = re.split(r'\^', value)
				# hang on to this because we are going to delete the field_name
				# variable as part of our work
				outer_fieldname = field_name
				for i in xrange(0, len(values)):
					field_name = special_subfields[ outer_fieldname ][i]
					v = values[i]
					rage_date = self._parse_tvrage_date( v )
					if rage_date:
						# convert them to a more standardized layout
						# it isn't ISO8901 but is more widely accepted
						v = self._render_tvrage_date( rage_date )
					results[ field_name ] = v
					# signal that we have already stored the field_name
					field_name = None
			elif field_name in date_fields and len(value) > 0:
				dt = self._parse_tvrage_date( value )
				if dt:
					value = self._render_tvrage_date( dt )
			if field_name:
				results[ field_name ] = value
		return results
	def _render_tvrage_date(self, rage_date):
		"""
		:param rage_date: the map containing ``mmm``,``dd``,``yyyy`` keys
		:returns: a string in a nice format
		"""
		return "%s %s %s" % \
			   (rage_date['dd'], rage_date['mmm'], rage_date['yyyy'])

	def _parse_tvrage_date(self, date_str):
		"""
		Tries to parse the given ``date_str`` as a TV-Rage formatted
		date (mmm/dd/yyyy).
		:param date_str: the string that might be in the TV-Rage format
		:returns: a map with keys ``mmm``,``dd``,``yyyy`` or None
		"""
		DATE_RE = re.compile(r'(...)/(\d\d)/(\d{4})')
		ma = DATE_RE.match( date_str )
		if not ma:
			return None
		result = {'mmm':ma.group(1),
				'dd':ma.group(2),
				'yyyy':ma.group(3)}
		return result

class SearchMovie(object):

	"""Takes a search string as an argument. Uses google's site search feature.
	It save's the results as a list of tuples of title and url.
	"""

	def __init__(self, searchString):

		self.searchString = searchString
		self.results = []
		self.opener = _MyOpener()
		quoted_query = urllib.quote_plus(searchString.strip())
		search_url = conf.strings["google_url"] % quoted_query
		fh = self.opener.open( search_url )
		self.feed = fh.read()
		fh.close()
		templist = re.findall(conf.strings["google_imdb_result_re"], self.feed, re.DOTALL)
		for i in templist:
			if len(i) > 1:
				self.results.append((re.sub(r"<[^>]+>","",decode(i[1])),i[0]))

	def __str__(self):
		return self.searchString

	def __unicode__(self):
		return unicode(self.searchString)

	def __repr__(self):
		return repr(self.results)

	def __getitem__(self, index):
		return self.results[index]

	def __len__(self):
		return len(self.results)

	def pop(self):
		return self.results.pop()

	def reverse(self):
		self.results.reverse()

class SearchImdb(object):

	"""Takes an imdb url as a parameter and returns an object with attributes scraped
	from the imdb page.
	"""

	def __init__(self,url):

		self.url = url
		self.data = {}
		self.errors = False
		self.director = ''
		self.shortdescription = ''
		self.tagline = ''
		self.title = ''
		self.genre = []
		self.releasedate = ''
		self.plotkeywords = []
		self.plot = ''
		self.seasons = []
		self.awards = ''
		self.writers = []
		self.rating = ''
		self.cast = []
		self.runtime = ''
		self.country = []
		self.mpaa = ''
		self.languages = []
		self.alsoknownas = []
		self.color = ''
		self.aspectratio = ''
		self.soundmix = []
		self.filminglocations = []
		self.company = []
		self.summary = []
		self.trailerurl = ''
		self.wikiurl = ''
		self.mediainfo = ''
		self.trivia = ''

		if not re.match(conf.strings["imdb_url_re"] ,self.url):
			raise URLError("Invalid URL")

		if self.url.endswith("/"):
			self.url = self.url[:-1]
		if not self.url.startswith("http://"):
			self.url = "http://" + self.url

		self.opener = _MyOpener()

		try:
			self.feed = self.opener.open(self.url)
		except:
			raise FetchError("Error connecting to IMDB")

		code = None
		if hasattr(self.feed, 'getcode'):
			# python 2.5 does not have getcode
			code = self.feed.getcode()
		if not code or code != 404:
			self.feed = self.feed.read()
		else:
			raise Error404("IMDB returned 404")

		self.__parsePage(self.feed)

	def __str__(self):
		return self.title

	def __unicode__(self):
		return unicode(self.title)

	def __getitem__(self, key):
		return self.data[key]

	def __setitem__(self, key, value):
		self.data[key] = value

	def overview(self, bbcode=False):

		"""Provides a short overview of the film or TV series. Optional argument turns on
		BBCode formatting.
		"""

		overview = ""
		if bbcode:
			format = ("[b]","[/b]")
		else:
			format = ("","")
		overview += "%sIMDB url:%s " % format + self.url
		if self.title:
			overview += "\n%sTitle:%s " % format + self.title
		if self.rating:
			overview += "\n%sRating:%s " % format + self.rating
		if self.director:
			if len(self.director) > 1:
				overview += "\n%sDirectors:%s " % format + " | ".join(self.director)
			else:
				overview += "\n%sDirector:%s " % format + " | ".join(self.director)
		if self.languages:
			if len(self.languages) > 1:
				overview += "\n%sLanguages:%s " % format + " | ".join(self.languages)
			else:
				overview += "\n%sLanguage:%s " % format + " | ".join(self.languages)
		#if self.aspectratio:
		#	overview += "\n%sAspect Ratio:%s " % format + self.aspectratio
		if self.releasedate:
			overview += "\n%sRelease Date:%s " % format + self.releasedate
		if self.seasons:
			overview += "\n%sSeasons:%s " % format + " | ".join(self.seasons)
		if self.genre:
			overview += "\n%sGenre:%s " % format + " | ".join(self.genre)
		if self.country:
			if len(self.country) > 1:
				overview += "\n%sCountries:%s " % format + " | ".join(self.country)
			else:
				overview += "\n%sCountry:%s " % format + " | ".join(self.country)
		return overview

	def __parsePage(self, page):

		"""Scrapes html from IMDB for information."""

		mdata = microdata.extract( page )
		if not mdata:
			raise ValueError("Unable to find any microdata in IMDB result")
		mitem = mdata[0]

		if 'http://schema.org/Movie/actors' in mitem:
			_cast = mitem['http://schema.org/Movie/actors']
			self.cast = re.split(r',', _cast)
		if 'http://schema.org/Movie/datePublished' in mitem:
			self.releasedate = mitem['http://schema.org/Movie/datePublished']
		if 'http://schema.org/Movie/description' in mitem:
			self.shortdescription = mitem['http://schema.org/Movie/description']
		if 'http://schema.org/Movie/director' in mitem:
			_dir = mitem['http://schema.org/Movie/director']
			self.director = re.split(r',', _dir)
		if 'http://schema.org/Movie/duration' in mitem:
			self.runtime = mitem['http://schema.org/Movie/duration']
		if 'http://schema.org/Movie/genre' in mitem:
			_genre = mitem['http://schema.org/Movie/genre']
			self.genre = re.split(r',', _genre)
		if 'http://schema.org/Movie/name' in mitem:
			self.title = mitem['http://schema.org/Movie/name']

		AGG_RATE_VALUE = 'http://schema.org/AggregateRating/ratingValue'
		aggRates = []
		if 'children' in mitem:
			aggRates = [x for x in mitem['children'] \
					if AGG_RATE_VALUE in x.keys() ]
		if aggRates:
			aggRate = aggRates[0]
			rateValue = aggRate[ AGG_RATE_VALUE ]
			rateTotal = None
			if 'http://schema.org/AggregateRating/bestRating' in aggRate:
				rateTotal = aggRate[
						'http://schema.org/AggregateRating/bestRating' ]
			if rateTotal:
				self.rating = '%s / %s' % ( rateValue, rateTotal )
			else:
				self.rating = rateValue

	def getSummary(self):

		"""returns the full summary for the movie"""
		if self.summary:
			return True

		try:
			fh = self.opener.open(self.url + "/plotsummary")
			synopsisPage = fh.read()
			fh.close()
		except:
			return False
		match = re.findall(conf.strings["imdb_summary_re"], synopsisPage, re.MULTILINE)
		if match:
			self.summary = match
			return True
		elif self.shortdescription:
			self.summary = [self.shortdescription]
			return True

	def findTrailer(self):

		"""searches for the trailer on youtube"""

		if not self.title:
			return False
		quoted_query = urllib.quote_plus(self.title.strip())
		the_url = conf.strings["google_youtube_url"] % quoted_query
		fh = self.opener.open( the_url )
		results = fh.read()
		fh.close()
		results = re.findall(conf.strings["google_youtube_result_re"], results)
		if results:
			for result in results:
				if re.search(self.title, result[1], re.IGNORECASE) and re.search(conf.strings["youtube_trailer_re"], result[1], re.IGNORECASE ):
					self.trailerurl = result[0]
					return True
			return False

	def findWiki(self):

		"""Tries in a somewhat rudimentary way to find the wikipedia url. If successful, it sets the attribute
		"self.wikiurl" and returns True. Otherwise, it returns False.
		"""

		searchstring = ""
		if self.title:
			searchstring += urllib.quote(self.title.strip().replace(" ","+"))
		if self.director:
			searchstring += urllib.quote("+" + self.director[0].strip().replace(" ","+"))
		if self.releasedate:
			match = re.findall(r"\d{4}", self.releasedate)
			if match:
				searchstring += "+" + match[0]
		if searchstring:
			the_url = conf.strings["google_wikipedia_url"] % searchstring
			fh = self.opener.open( the_url )
			results = fh.read()
			fh.close()
			links = re.findall(conf.strings["wikipedia_url"], results)
			if links:
				self.wikiurl = urlparse.urljoin(links[0], urllib.quote(urlparse.urlparse(links[0]).path))
				return True
		return False

def findMediaInfo( path ):
	"""Returns the mediainfo text if possible, or None otherwise.
	BE AWARE that I will sys.exit upon ``OSError``.
	"""
	mediainfo = None
	try:
		if os.name=="nt":
			##Must pass Shell=True on Windows, but this is a potential security issue
			mediainfo = subprocess.Popen([r"mediainfo",path], shell=True, stdout=subprocess.PIPE).communicate()[0]
		else:
			mediainfo = subprocess.Popen([r"mediainfo",path], stdout=subprocess.PIPE).communicate()[0]
	except OSError:
		sys.stderr.write("Error: Media Info not installed, refer to http://mediainfo.sourceforge.net/en for installation")
		exit(1)
	return mediainfo

class Imgur(object):
	def __init__(self, path, shots = 2):
		self.path = path
		self.imageurl = []
		self.key = conf.strings["imgur_key"]
		self.tries = 0
		self.duration = ''
		self.ffmpeg = ''
		if shots < 2:
			self.shots = 2
			sys.stderr.write('Number of screenshots increased to 2\n')
		elif shots > 7:
			self.shots = 7
			sys.stderr.write('Number of screenshots limited to 7\n')
		else:
			self.shots = shots
        

	def getDuration(self):
		try:
			self.ffmpeg = subprocess.Popen([r"ffmpeg","-i",self.path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		except OSError:
			sys.stderr.write("Error: Ffmpeg not installed, refer to http://www.ffmpeg.org/download.html for installation")
			exit(1)
		self.duration = re.findall(r'Duration:\D(\d{2}):(\d{2}):(\d{2})', self.ffmpeg.stdout.read())
		self.duration = int(self.duration[0][0]) * 3600 + int(self.duration[0][1]) * 60 + int(self.duration[0][2])

	def upload(self):
		self.getDuration()
		# Take screenshots at even increments between 20% and 80% of the duration
		stops = range(20,81,60/(self.shots-1))
		imgs = [ ]
		try:
			count=0
			for stop in stops:
				imgs.append(tempdir()+"screen%d.png" % count)
				subprocess.Popen([r"ffmpeg","-ss",str((self.duration * stop)/100), "-vframes", "1", "-i", self.path , "-y", "-sameq", "-f", "image2", imgs[-1] ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).wait()
				count+=1
		except OSError:
			sys.stderr.write("Error: Ffmpeg not installed, refer to http://www.ffmpeg.org/download.html for installation")
			exit(1)
		opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
		
		try:
			for img in imgs:
				params = ({'key' : self.key.decode('utf-8').encode('utf-8'), 'image' : open(img, "rb")})
				socket = opener.open("http://api.imgur.com/2/upload.json", params)
				json_str = socket.read()
				if hasattr(json,'loads'):
					read = json.loads( json_str )
				elif hasattr(json,'load'):
					read = json.loads( json_str )
				else:
					err_msg = "I cannot decipher your `json`;" + \
						"please report the following output to the bB forum:" + \
						("%s" % dir(json))
					raise Exception( err_msg )
				self.imageurl.append(read['upload']['links']['original'])
				socket.close()
				os.remove(img)
			return True
		except urllib2.URLError, s:
			if self.tries < 3:
				self.tries += 1
				sys.stderr.write('Connection timed out, retrying to upload screenshots to imgur. This is try: ')
				sys.stderr.write(str(self.tries))
				sys.stderr.write('\n')
				sys.stderr.write(str(s))
				self.upload()
			return True

def updateConfig():
	update_url = "https://raw.github.com/Ichabond/Pythonbits/master/config.xml"
	opener = _MyOpener()
	newconf = opener.open(update_url)
	if newconf.info()["Status"]=="200 OK":
		fh = open(tempdir()+"config.xml", "w")
		fh.write(newconf.read())
		fh.close()
		print "Config file succesfully updated"
	else:
		__logerror("Cannot update config file.")
	newconf.close()
	os.chmod(tempdir()+"config.xml", 0777)

if __name__ == "__main__":
	from optparse import OptionParser

	usage = 'Usage: %prog [OPTIONS] "MOVIENAME/SERIESNAME" FILENAME'
	parser = OptionParser(usage=usage, version="%%prog %s" % __version_str__)
	parser.add_option("-e", "--episode", type="string", action="store", dest="tv_episode",
		help="Provides the TV episode identifier (1x2 or S01E02)")
	parser.add_option("-u", "--update", action="store_true", dest="update",
		help="update the config hints from the central github repository")
	parser.add_option("-s", "--screenshots", type="int", action="store", dest="screenshots", help="Set the amount of screenshots, max 7")
	options, args = parser.parse_args()

	tv_episode = None
	if options.tv_episode:
		matchers = [
				re.compile(r'(\d+)x(\d+)'),
				re.compile(r'(?i)s(\d+)e(\d+)')
				]
		for matcher in matchers:
			ma = matcher.match(options.tv_episode)
			if ma:
				tv_episode = ( int(ma.group(1)), int(ma.group(2)) )
				break
		if not tv_episode:
			print >> sys.stderr, \
				"Unable to decipher your tv-episode \"%s\"" % options.tv_episode
		# print "TV-Episode: %s" % str(tv_episode)
	if options.update:
		print "Updating Configfile"
		updateConfig()
		sys.exit(0)
	conf = PythonbitsConfig()
	conf.set_location(tempdir()+"config.xml")
	try:
		conf.read()
	except:
		updateConfig()

	search_string = args[0]
	filename = args[1]

	movie = None
	if tv_episode:
		results = SearchTV(search_string, tv_episode).result
	else:
		results = SearchMovie(search_string).results
		if results:
			movie = SearchImdb(results[0][1])
		else:
			__logerror("No films found.\n")
			exit(1)
	if movie and movie.getSummary():
		print "[b]Description:[/b]"
		print "[quote]%s[/quote]\n" % movie.summary[0]
	print "[b]Information:[/b]"
	print "[quote]"
	if movie:
		if movie.findWiki():
			print "Wikipedia url: %s" % movie.wikiurl
		if movie.findTrailer():
			print "Trailer: %s" % movie.trailerurl
		print movie.overview()
	elif tv_episode:
		interesting_fields = [
			'Classification',
			'Country',
			'Ended',
			'Episode URL',
			'Genres',
			'Network',
			'Premiered',
			'Runtime',
			'Episode Description',
			'Show Name',
			'Show URL',
			'Started',
			'Status'
		]
		for field_name in interesting_fields:
			if not field_name in results:
				continue
			v = results[ field_name ]
			print "[b]%s[/b]: %s" % (field_name, v)
	print "[/quote]"
	print "[b]Screenshots:[/b]"
	if options.screenshots:
		imgur = Imgur(filename,int(options.screenshots))
	else:
		imgur = Imgur(filename)
	if imgur.upload():
		print "[quote][align=center]" 
		for url in imgur.imageurl:
			print "[img=%s]" % url
		print "[/align][/quote]"
	mediainfo = findMediaInfo(filename)
	if mediainfo:
		print "[mediainfo]\n%s\n[/mediainfo]" % mediainfo
