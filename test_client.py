import urllib2, json
import httplib, mimetypes
import MultipartPostHandler

socket =  urllib2.urlopen("http://min.us/api/CreateGallery")
read = json.loads(socket.read(), encoding='latin-1')
test1 = read["reader_id"].decode('utf-8').encode('utf-8')
test2 = read["editor_id"].decode('utf-8').encode('utf-8')
test3 = read["key"].decode('utf-8').encode('utf-8')
print test1, test2, test3

opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
params = ({'editor_id' : test2, 'key' : test3, 'filename' : open("image.jpg", "rb")})
paramsi = ({'key' : "bc1d6b50ff5dc9a563ec01583bbd5677", 'image' : open("image.jpg", "rb")})
print opener.open("http://api.imgur.com/2/upload.json", paramsi).read()
print opener.open("http://min.us/api/UploadItem", params).read()
