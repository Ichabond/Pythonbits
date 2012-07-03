#!/usr/bin/env python
# encoding: utf-8
"""
ImageUploader.py

Created by Ichabond on 2012-07-01.
"""

import json, urllib2, MultipartPostHandler, re

class Upload(object):
	
	def __init__(self, filelist):
		self.images = filelist
		self.imageurl = []
		
	def upload(self):
		opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
		matcher = re.compile(r'http(s)*://')
		try:
			for image in self.images:
				if matcher.match(image):
					params = ({'url' : image})
				else:
					params = ({'ImageUp' : open(image, "rb")})
				socket = opener.open("https://images.baconbits.org/upload.php", params)
				json_str = socket.read()
				if hasattr(json, 'loads') or hasattr(json, 'read'):
					read = json.loads(json_str)
				else:
					err_msg = "I cannot decipher the provided json\n" + \
						"Please report the following output to the relevant bB forum: \n" + \
						("%s" % dir(json))
				self.imageurl.append("https://images.baconbits.org/images/" + read["ImgName"])
		except Exception as e:
			print e	
		return self.imageurl