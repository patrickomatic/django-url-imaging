import urllib, urllib2, os, hashlib, re, datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from urlimaging.image import *


LATIN_ASCII_MAP = { 
	0xc0: 'A', 0xc1: 'A', 0xc2: 'A', 0xc3: 'A', 0xc4: 'A', 0xc5: 'A', 0xc6: 'Ae', 0xc7: 'C', 
	0xc8: 'E', 0xc9: 'E', 0xca: 'E', 0xcb: 'E', 0xcc: 'I', 0xcd: 'I', 0xce: 'I', 0xcf: 'I', 
	0xd0: 'Th', 0xd1: 'N', 0xd2: 'O', 0xd3: 'O', 0xd4: 'O', 0xd5: 'O', 0xd6: 'O', 0xd8: 'O', 
	0xd9: 'U', 0xda: 'U', 0xdb: 'U', 0xdc: 'U', 0xdd: 'Y', 0xde: 'th', 0xdf: 'ss', 0xe0: 'a', 
	0xe1: 'a', 0xe2: 'a', 0xe3: 'a', 0xe4: 'a', 0xe5: 'a', 0xe6: 'ae', 0xe7: 'c', 0xe8: 'e', 
	0xe9: 'e', 0xea: 'e', 0xeb: 'e', 0xec: 'i', 0xed: 'i', 0xee: 'i', 0xef: 'i', 0xf0: 'th', 
	0xf1: 'n', 0xf2: 'o', 0xf3: 'o', 0xf4: 'o', 0xf5: 'o', 0xf6: 'o', 0xf8: 'o', 0xf9: 'u', 
	0xfa: 'u', 0xfb: 'u', 0xfc: 'u', 0xfd: 'y', 0xfe: 'th', 0xff: 'y', 0xa1: '!', 
	0xa2: '{cent}', 0xa3: '{pound}', 0xa4: '{currency}', 0xa5: '{yen}', 0xa6: '|', 
	0xa7: '{section}', 0xa8: '{umlaut}', 0xa9: '{C}', 0xaa: '{^a}', 0xab: '<<', 0xac: '{not}', 
	0xad: '-', 0xae: '{R}', 0xaf: '_', 0xb0: '{degrees}', 0xb1: '{+/-}', 0xb2: '{^2}', 
	0xb3: '{^3}', 0xb4: "'", 0xb5: '{micro}', 0xb6: '{paragraph}', 0xb7: '*', 
	0xb8: '{cedilla}', 0xb9: '{^1}', 0xba: '{^o}', 0xbb: '>>', 0xbc: '{1/4}', 0xbd: '{1/2}', 
	0xbe: '{3/4}', 0xbf: '?', 0xd7: '*', 0xf7: '/', 0x00d7: 'x', 
}


def latin1_to_ascii(uni):
	r = ''
	for i in uni:
		if LATIN_ASCII_MAP.has_key(ord(i)):
			r += LATIN_ASCII_MAP[ord(i)]
		elif ord(i) >= 0x80:
			pass
		else:
			r += str(i)
	return r



def domain_name(url):
	return re.sub(r'/.*$', '', re.sub(r'^(http://?)?', '', url)).lower()


def url_path(url):
	return re.sub(r'^[^/]+', '', re.sub(r'^http://?', '', url))


class Site(models.Model):
	domain_name = models.CharField(max_length=255, unique=True, db_index=True) 

	def get_absolute_url(self):
		return self.domain_name

	def __unicode__(self):
		return self.domain_name


class ModifiedImage(models.Model):
	hash = models.CharField(max_length=56, unique=True, db_index=True) 
	ext = models.CharField(max_length=10, db_index=True)
	operations = models.CharField(max_length=4096) 
	last_modified = models.CharField(max_length=255, null=True)
	last_checked = models.DateTimeField(db_index=True, default=datetime.datetime.now())
	original_location = models.CharField(max_length=4096)
	original_file_hash = models.CharField(max_length=56)
	site = models.ForeignKey(Site)
	size = models.PositiveIntegerField(default=0)


	def delete(self):
		settings.IMAGE_STORAGE.delete_image(self.hash)

		models.Model.delete(self)

	def refresh(self):
		cr = CommandRunner(self.get_absolute_url()[1:])
		if cr.todo:
			self.delete()
			if cr.run_commands():
				return True

		return False

	def get_absolute_url(self):
		return '/' + self.operations + self.site.domain_name + self.original_location

	def __unicode__(self):
		return self.get_absolute_url()


# XXX use a setting for the directory
def file_location(hash, ext):
	return '/tmp/' + hash + ext


def sanitize_url(url):
	domain, url = domain_name(url), url_path(url).encode('utf8')
	return 'http://' + domain + urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")


def valid_image_path(url):
	return re.match(r'^(http://?)?[\w\-\.]+\.\w+(\:\d+){0,1}/.+$', url, re.I)


class ImageNotFoundException(Exception):
	pass


class CommandRunner:
	def __init__(self, url=None):
		self.todo = []
		self.url = ""
		self.filename = ""
		self.hashed_filename = ""
		self.ext = ""
		self.hash = ""
		self.operations = ""

		if url: self.parse_url(url)


	def parse_url(self, url):
		did_op = True

		# apply the operations to the url until none are left
		while did_op:
			did_op = False
			for op in COMMANDS:
				m = re.match(op['regex'], url)
				if m:
					self.operations += m.group().lower()
					self.todo.append((op['fn'], m.groups()))
					url = re.sub(op['regex'], '', url)
					did_op = True
					break


		if self.todo and valid_image_path(url):
			self.url = sanitize_url(url)
			self.ext = os.path.splitext(re.sub(r'\?.+$', '', url))[-1]
			if not self.ext:
				self.ext = '.jpg'

			self.hash = hashlib.sha224(self.operations + latin1_to_ascii(url)).hexdigest()
			self.filename = file_location(self.hash, self.ext)
			self.hashed_filename = "%s%s" % (self.hash, self.ext)
		else:
			self.todo = []


	def get_image(self, image):
		""" Get the image and return true or false if it's changed or not.  It can tell
		    if it's been used by either using the last-modified header saved from a previous
		    request, or if that doesn't exist, it compares a hash of the file's contents """
		image.last_checked = datetime.datetime.now()
		# if it exists, always save here that it's been checked
		if image.id: image.save()

		request = urllib2.Request(self.url)

		if image.last_modified:
			request.add_header('If-Modified-Since', image.last_modified)

		try:
			remote = urllib2.build_opener().open(request)
		except urllib2.HTTPError as e:
			if e.code == 404: raise ImageNotFoundException()
			# 304 Not Modified
			return False
		except urllib2.URLError as e:
			# requesting host down?
			return False

		content_type = remote.info().getheader('content-type').lower()
		if not content_type.startswith('image/') \
				and not content_type.endswith("/octet-stream"):
			remote.close()
			raise ImageNotFoundException()

		hasher = hashlib.sha224()
		local = open(self.filename, 'w')

		# read file in 4K chunks and make a hash of it
		size = 0
		while True:
			chunk = remote.read(4096)
			if not chunk: break

			size += len(chunk)

			# don't process images larger than 10 MBS
			if size > TEN_MBS: return False

			local.write(chunk)
			hasher.update(chunk)

		local.close()
		remote.close()

		remote_file_hash = hasher.hexdigest()
		if image.original_file_hash == remote_file_hash:
			# compared the hashes and they are still the same (no change)
			os.unlink(self.filename)
			return False

		# if it's changed, delete the previous
		if image.id:
			image.delete()

		image.original_file_hash = remote_file_hash
		image.last_modified = remote.info().getheader('last-modified')

		return True


	def run_commands(self, user=None):
		check_remote_image = False
		try:
			image = ModifiedImage.objects.get(hash=self.hash)	
		except ModifiedImage.DoesNotExist:
			# need to create the image
			image = ModifiedImage(hash=self.hash, \
					original_location=url_path(self.url), \
					operations=self.operations, ext=self.ext)

			# do we need to create the domain too?
			try:
				site = Site.objects.get(domain_name=domain_name(self.url))

			except Site.DoesNotExist:
				site = Site(domain_name=domain_name(self.url))
				site.save()

			image.site = site
			check_remote_image = True
		else:
			if settings.USE_TZ:
				two_hours_ago = timezone.make_aware(datetime.datetime.now(), timezone.get_default_timezone()) - datetime.timedelta(hours=2)
			else:
				two_hours_ago = datetime.datetime.now() - datetime.timedelta(hours=2)
			check_remote_image = image.last_checked < two_hours_ago


		if check_remote_image and self.get_image(image):
			# apply all of the transformations
			for fn, group in self.todo:
				try: 
					fn(self.filename, *group)
				except ValueError as e:
					break

			settings.IMAGE_STORAGE.save_image(self.hashed_filename, self.filename)
			image.size = os.path.getsize(self.filename)

			os.unlink(self.filename)

		if check_remote_image:
			image.save()

		return settings.IMAGE_STORAGE.get_image_url(self.hashed_filename)
