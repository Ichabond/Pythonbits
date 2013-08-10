#!/usr/bin/env python
# encoding: utf-8
"""
Ffmpeg.py

Created by Tom Strickx on 2012-07-01.
Copyright (c) 2012 Baconseed. All rights reserved.
"""

import os, subprocess, sys, re

from tempfile import mkdtemp

class FFMpeg (object):
	
	def __init__(self, filepath):
		self.file = filepath
		self.ffmpeg = None
		self.duration = None
		self.tempdir = mkdtemp(prefix="pythonbits-")+os.sep
		
	def getDuration(self):
			try:
				self.ffmpeg = subprocess.Popen([r"ffmpeg","-i",self.file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			except OSError:
				sys.stderr.write("Error: Ffmpeg not installed, refer to http://www.ffmpeg.org/download.html for installation")
				exit(1)
			ffmpeg_out = self.ffmpeg.stdout.read()
			ffmpeg_duration = re.findall(r'Duration:\D(\d{2}):(\d{2}):(\d{2})', ffmpeg_out)
			if not ffmpeg_duration:
				# the odds of a filename collision on an md5 digest are very small
				out_fn = '%s.txt' % md5(ffmpeg_out).hexdigest()
				err_f = open(out_fn, 'wb')
				err_f.write( ffmpeg_out )
				err_f.close()
				err_msg = ("Expected ffmpeg to mention 'Duration' but it did not;\n"+
					"Please copy the contents of '%s' to http://pastebin.com/\n"+
					" and send the pastebin link to the bB forum.") % \
						out_fn
				sys.stderr.write( err_msg )
			dur = ffmpeg_duration[0]
			dur_hh = int(dur[0])
			dur_mm = int(dur[1])
			dur_ss = int(dur[2])
			self.duration = dur_hh * 3600 + dur_mm * 60 + dur_ss
				
	def takeScreenshots(self, shots):
		self.getDuration()
		stops = range(20, 81, 60/(shots-1))
		imgs = []
		try:
			for stop in stops:
				imgs.append(self.tempdir+"screen%s.png" % stop)
				subprocess.Popen([r"ffmpeg","-ss",str((self.duration * stop)/100), "-vframes", "1",
									"-i", self.file , "-y", "-qscale", "0",  "-f", "image2", imgs[-1] ], 
									stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
		except OSError:
			sys.stderr.write("Error: Ffmpeg not installed, refer to http://www.ffmpeg.org/download.html for installation")
			exit(1)
		return imgs

