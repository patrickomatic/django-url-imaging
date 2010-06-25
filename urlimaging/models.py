import urllib, urllib2, os, hashlib, re, sys, datetime, time
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import F

from boto.s3.connection import S3Connection
from boto.s3.key import Key, S3DataError

from urlimaging.image.image import *


FREE_BYTES = 50 * 1024 * 1024

# XXX move into __init.py__
conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
bucket = conn.get_bucket(settings.S3_BUCKET)


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
	operations = models.CharField(max_length=4096) 
	last_modified = models.CharField(max_length=255, null=True)
	last_checked = models.DateTimeField(db_index=True, default=datetime.datetime.now())
	original_location = models.CharField(max_length=4096)
	original_file_hash = models.CharField(max_length=56)
	site = models.ForeignKey(Site)
	size = models.PositiveIntegerField(default=0)


	def delete(self):
		k = Key(bucket, self.hash)
		k.delete()
		k.close()

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
	domain, url = domain_name(url), url_path(url)
	return 'http://' + domain + urllib.quote(url)


def valid_image_path(url):
	return re.match(r'^(http://?)?[\w\-\.]+\.\w+/.+$', url, re.I)


def retry(times, ex):
	""" A decorator which can be called as:

		@retry(5, S3DataError)
		def fn():
			pass

	    and will call fn and if it throws an exception, it will keep
	    trying 5 times. """
	def retry_wrap(fn):
		def fn_wrap(*args, **kwargs):
			for i in range(times-1):
				try:
					return fn(*args, **kwargs)
				except ex:
					pass
			return fn(*args, **kwargs)
		return fn_wrap
	return retry_wrap


class CommandRunnerException(Exception):
	display_image = None

class ImageNotFoundException(CommandRunnerException):
	display_image = None


class CommandRunner:
	def __init__(self, url=None):
		self.todo = []
		self.url = ""
		self.filename = ""
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
			self.ext = os.path.splitext(url)[-1]
			if not self.ext:
				self.ext = '.jpg'

			self.hash = hashlib.sha224(self.operations + url).hexdigest()
			self.filename = file_location(self.hash, self.ext)
		else:
			self.todo = []


	def get_image(self, image):
		""" Get the image and return true or false if it's changed or not.  It can tell
		    if it's been used by either using the last-modified header saved from a previous
		    request, or if that doesn't exist, it compares a hash of the file's contents """
		image.last_checked = datetime.datetime.now()

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

		if not remote.info().getheader('content-type').lower().startswith('image/'):
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
		k = Key(bucket, self.hash)
			
		check_remote_image = False
		try:
			image = ModifiedImage.objects.get(hash=self.hash)	
		except ModifiedImage.DoesNotExist:
			# need to create the image
			image = ModifiedImage(hash=self.hash, \
					original_location=url_path(self.url), \
					operations=self.operations)

			# do we need to create the domain too?
			try:
				site = Site.objects.get(domain_name=domain_name(self.url))

			except Site.DoesNotExist:
				site = Site(domain_name=domain_name(self.url))
				site.save()

			image.site = site
			check_remote_image = True
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

			self.set_s3_contents(k)
			image.size = os.path.getsize(self.filename)

			os.unlink(self.filename)

		image.save()

		ret = k.generate_url(settings.S3_EXPIRES, 'GET', 
				{'Cache-Control': 'public, max-age=7200',
				'Expires': time.asctime(time.gmtime(time.time() + 7200)) })
		k.close()

		return ret

	@retry(3, S3DataError)
	def set_s3_contents(self, key):
		key.set_contents_from_filename(self.filename, 
				{'Cache-Control': 'public, max-age=7200',
				'Expires': time.asctime(time.gmtime(time.time() + 7200)) })
