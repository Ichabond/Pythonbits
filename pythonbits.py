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
import httplib
import mimetypes
import urlparse
import sys
import re
import subprocess
import tempfile
import os
import base64
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

class pythonbits_config:
	"""Class for holding pythonbits config strings. read() or create_dom() must be called before first use. Access strings through obj.strings[key]"""
	def __init__(self):
		self.strings={}
		self.file=tempdir()+"config.xml"
		if not os.path.exists(self.file):
			update_url = "https://github.com/Ichabond/Pythonbits/raw/master/config.xml"
			opener = _MyOpener()
			nconf = opener.open(update_url)
			if (nconf.info()["Status"]=="200 OK"):
				open(tempdir()+"config.xml", "w").write(nconf.read())
			else:
				__logerror("Cannot update config file.")
			
		
	def __del__(self):
		self.file.close()

	def read(self, file=0):
		if(file==0):
			file=self.file
		self.xml = parse(file)
		self.load_strings()

	def write(self, file=0):
		if(file==0):
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

class search(object):

	"""Takes a search string as an argument. Uses google's site search feature.
	It save's the results as a list of tuples of title and url.
	"""

	def __init__(self, searchString):

		self.searchString = searchString
		self.results = []
		self.opener = _MyOpener()
		self.feed = self.opener.open(conf.strings["google_url"] % searchString.strip().replace(" ", "+")).read()
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

class imdb(object):

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
		self.summary = ''
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

		if self.feed.getcode() != 404:
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

		# director
		self.director = re.findall(conf.strings["imdb_director_re"], page, re.MULTILINE)
		self.__setitem__("director", self.director)

		# tagline
		match = re.findall(conf.strings["imdb_tagline_re"], page, re.DOTALL)
		if match:
			self.tagline = decode(match[0])
		self.__setitem__("tagline", self.tagline)
		
		# short description
		match = re.findall(conf.strings["imdb_description_re"], page,re.MULTILINE)
		if match:
			self.shortdescription = decode(match[0])
		self.__setitem__("shortdescription", self.shortdescription)

		# plot
		#match = re.findall(conf.strings["imdb_plot_re"], page, re.MULTILINE)
		#i3f match:
		#	self.plot = match[0]
		#self.__setitem__("plot", self.plot)

		# title
		match = re.findall(conf.strings["imdb_title_re"], page)
		if match:
			self.title = decode(match[0].strip())
		self.__setitem__("title", self.title)

		# genre
		self.genre = re.findall(conf.strings["imdb_genre_re"], page, re.MULTILINE)
		self.__setitem__("genre", self.genre)

		# release date
		match = re.findall(conf.strings["imdb_releasedate_re"], page, re.MULTILINE)
		if match:
			self.releasedate = match[0]
		self.__setitem__("releasedate", self.releasedate)

		# keywords
		#self.plotkeywords = map(decode, re.findall(conf.strings["imdb_plotkeywords_re"],page, re.MULTILINE))
		#self.__setitem__("plotkeywords", self.plotkeywords)

		# awards
		#match = re.findall(conf.strings["imdb_awards_re"], page, re.MULTILINE)
		#if match:
		#	self.awards = decode(match[0].replace('\n',' ').strip())
		#self.__setitem__("awards", self.awards)

		# writers
		self.writers = map(decode, re.findall(conf.strings["imdb_writers_re"], page, re.MULTILINE))
		self.__setitem__("writers", self.writers)

		# rating
		match = re.findall(conf.strings["imdb_rating_re"], page, re.MULTILINE)
		if match:
			self.rating = match[0]
		self.__setitem__("rating", self.rating)

		# cast
		#castsearch = re.compile(conf.strings["imdb_castsearch_re"], re.DOTALL)
		#self.cast = re.findall( castsearch, page) 
		#x = 0
		#for member in self.cast:
		#	if not member[2]:
		#		self.cast[x] = tuple(map(decode,member[0:2]))
		#	x=x+1
		#self.__setitem__("cast", self.cast)

		# runtime
		match = re.findall(conf.strings["imdb_runtime_re"], page, re.MULTILINE)
		if match:
			self.runtime = decode(match[0].strip())
		self.__setitem__("runtime", self.runtime)

		# countries
		self.country = map(decode, re.findall(conf.strings["imdb_country_re"], page, re.MULTILINE))
		self.__setitem__("country", self.country)

		# mpaa rating
		#match = map(decode, re.findall(conf.strings["imdb_mpaa_re"], page, re.MULTILINE))
		#if match:
		#	self.mpaa = decode(match[0])
		#self.__setitem__("mpaa", self.mpaa)

		# languages
		self.languages = map(decode, re.findall(conf.strings["imdb_languages_re"], page, re.MULTILINE))
		self.__setitem__("languages", self.languages)

		# also known as
		#match = re.findall(conf.strings["imdb_alsoknownas_re"], page, re.MULTILINE)
		#if match:
		#	templist = decode(match[0]).split('<br>')
		#	for i in templist:
		#		if i.strip():
		#			self.alsoknownas.append(i.strip())
		#self.__setitem__("alsoknownas", self.alsoknownas)
			

		# color
		#match = re.findall(conf.strings["imdb_color_re"], page, re.MULTILINE)
		#if match:
		#	self.color = match[0]
		#self.__setitem__("color", self.color)

		# aspect ratio
		#match = re.findall(conf.strings["imdb_aspectratio_re"], page, re.MULTILINE)
		#if match:
		#	self.aspectratio = match[0].strip()
		#self.__setitem__("aspectratio", self.aspectratio)

		# sound mixes
		#self.soundmix = re.findall(conf.strings["imdb_soundmix_re"], page, re.MULTILINE)
		#self.__setitem__("soundmix", self.soundmix)

		# filming locations
		self.filminglocations = map(decode, re.findall(conf.strings["imdb_filminglocations_re"],page, re.MULTILINE))
		self.__setitem__("filminglocations", self.filminglocations)

		# companies
		#self.company = map(decode, re.findall(conf.strings["imdb_company_re"], page, re.MULTILINE))
		#self.__setitem__("company", self.company)

		# trivia
		#match = re.findall(conf.strings["imdb_trivia_re"], page, re.DOTALL)
		#if match:
		#	self.trivia = decode(re.sub(conf.strings["imdb_trivia_more_re"],'', match[0], re.DOTALL).replace("\n","").strip())
		#self.__setitem__("trivia", self.trivia)

		# seasons
		self.seasons = re.findall(conf.strings["imdb_seasons_re"], page )
		self.__setitem__("seasons", self.seasons)


	def getSummary(self):

		"""returns the full summary for the movie"""
		if self.summary:
			return True

		try:
			synopsisPage = self.opener.open(self.url + "/plotsummary").read()
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
		results = self.opener.open(conf.strings["google_youtube_url"] +\
								   urllib.quote(self.title.strip().replace(" ","+"))).read()
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
			results = self.opener.open(conf.strings["google_wikipedia_url"] +\
								   searchstring).read()
			links = re.findall(conf.strings["wikipedia_url"], results)
			if links:
				self.wikiurl = urlparse.urljoin(links[0], urllib.quote(urlparse.urlparse(links[0]).path))
				return True
		return False

	def findMediaInfo(self, path):
		try:
			if(os.name=="nt"):
				##Must pass Shell=True on Windows, but this is a potential security issue
				self.mediainfo = subprocess.Popen([r"mediainfo",path], shell=True, stdout=subprocess.PIPE).communicate()[0]
			else:
				self.mediainfo = subprocess.Popen([r"mediainfo",path], stdout=subprocess.PIPE).communicate()[0]
		except OSError:
			sys.stderr.write("Error: Media Info not installed, refer to http://mediainfo.sourceforge.net/en for installation")
			exit(1)
		return True

class Imgur(object):
	def __init__(self, path):
		self.path = path
		self.imageurl = ['', '']
		self.key = conf.strings["imgur_key"]
		self.tries = 0
		self.duration = ''
		self.ffmpeg = ''
		
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
		try:
			subprocess.Popen([r"ffmpeg","-ss",str((self.duration * 2)/10), "-vframes", "1", "-i", self.path , "-y", "-sameq", "-f", "image2", tempdir()+"screen1.png" ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).wait()
			subprocess.Popen([r"ffmpeg","-ss",str((self.duration * 8)/10), "-vframes", "1", "-i", self.path , "-y", "-sameq", "-f", "image2", tempdir()+"screen2.png" ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).wait()
		except OSError:
			sys.stderr.write("Error: Ffmpeg not installed, refer to http://www.ffmpeg.org/download.html for installation")
			exit(1)
		opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
		params1 = ({'key' : self.key.decode('utf-8').encode('utf-8'), 'image' : open(tempdir()+'screen1.png', "rb")})
		params2 = ({'key' : self.key.decode('utf-8').encode('utf-8'), 'image' : open(tempdir()+'screen2.png', "rb")})
		try:
			socket = opener.open("http://api.imgur.com/2/upload.json", params1)
			read = json.loads(socket.read())
			self.imageurl[0] = read['upload']['links']['original']
			socket.close()
			socket = opener.open("http://api.imgur.com/2/upload.json", params2)
			read = json.loads(socket.read())
			self.imageurl[1] = read['upload']['links']['original']
			socket.close()
			os.remove(tempdir()+'screen1.png')
			os.remove(tempdir()+'screen2.png')
			return True
		except urllib2.URLError as s:
			if self.tries < 3:
				self.tries += 1
				sys.stderr.write('Connection timed out, retrying to upload screenshots to imgur. This is try: ')
				sys.stderr.write(str(self.tries))
				sys.stderr.write('\n')
				self.upload()
			return True


if __name__ == "__main__":
	from optparse import OptionParser

	usage = 'Usage: %prog [OPTIONS] "MOVIENAME/SERIESNAME" FILENAME'
	parser = OptionParser(usage=usage, version="%%prog %s" % __version_str__)
	parser.add_option("-u", "--update", action="store_true", dest="update",
		help="update the config hints from the central github repository")
	options, args = parser.parse_args()
	if len(args) != 2:
		parser.error("2 arguments expected, got %d. Use --help for additional info." % len(args))

	if options.update:
		try:
			conf = pythonbits_config()
			conf.set_location(tempdir()+"config.xml")
			conf.read()
			update_url = conf.strings["update_url"]
		except:
			update_url = "https://github.com/Ichabond/Pythonbits/raw/master/config.xml"
			del conf
			opener = _MyOpener()
			newconf = opener.open(update_url)
			if (newconf.info()["Status"]=="200 OK"):
				open(tempdir()+"config.xml", "w").write(newconf.read())
			else:
				__logerror("Cannot update config file.")           
	conf = pythonbits_config()
	conf.set_location(tempdir()+"config.xml")
	try:
		conf.read()
	except:
		update_url = "https://github.com/Ichabond/Pythonbits/raw/master/config.xml"
		opener = _MyOpener()
		conf = opener.open(update_url)
		if (conf.info()["Status"]=="200 OK"):
			open(tempdir()+"config.xml", "w").write(conf.read())
		else:
			__logerror("Cannot update config file.")

	filename = args[1]
	results = search(args[0]).results
	if results:
		movie = imdb(results[0][1])
		imgur = Imgur(filename)
	else:
		__logerror("No films found.\n")
		exit(1)
	print "[b]Description:[/b]"
	if movie.getSummary():
		print "[quote]%s[/quote]\n" % movie.summary[0]
	print "[b]Information:[/b]"
	print "[quote]"
	if movie.findWiki():
		print "Wikipedia url: %s" % movie.wikiurl
	if movie.findTrailer():
		print "Trailer: %s" % movie.trailerurl
	print movie.overview(False) + "[/quote]"
	print "[b]Screenshots:[/b]"
	if imgur.upload():
		print "[quote][align=center][img=%s]" % imgur.imageurl[0]
		print "\n[img=%s][/align][/quote]" % imgur.imageurl[1]
	if movie.findMediaInfo(filename):
		print "[mediainfo] %s [/mediainfo]" % movie.mediainfo
