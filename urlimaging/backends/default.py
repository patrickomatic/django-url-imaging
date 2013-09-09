import time, shutil, os

from django.conf import settings


class ImageStorage:
	def delete_image(self, hash):
		raise Exception('delete_image not implemented')

	def save_image(self, filename):
		raise Exception('save_image not implemented')

	def get_image_url(self, hash):
		raise Exception('get_image_url not implemented')

	def get_required_settings(self):
		raise Exception('get_required_settings not implemented')


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


class S3ImageStorage(ImageStorage):
	def __init__(self):
		from boto.s3.connection import S3Connection

		self.connection = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
		self.bucket = self.connection.get_bucket(settings.S3_BUCKET_NAME)


	def delete_image(self, hash):
		from boto.s3.key import Key

		k = Key(self.bucket, hash)
		k.delete()
		k.close()


	@retry(3, Exception)
	def save_image(self, hash, filename):
		from boto.s3.key import Key

		key = Key(self.bucket, hash)
		key.set_contents_from_filename(filename, 
				{'Cache-Control': 'public, max-age=%d' % settings.S3_EXPIRES,
				'Expires': time.asctime(time.gmtime(time.time() + settings.S3_EXPIRES)) })
		key.close()


	def get_image_url(self, hash):
		from boto.s3.key import Key

		key = Key(self.bucket, hash)

		ret = key.generate_url(settings.S3_EXPIRES, 'GET', 
				{'Cache-Control': 'public, max-age=%d' % settings.S3_EXPIRES,
				'Expires': time.asctime(time.gmtime(time.time() + settings.S3_EXPIRES)) })
		key.close()

		return ret


	def get_required_settings(self):
		return ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'S3_BUCKET_NAME']


class LocalImageStorage(ImageStorage):
	def get_storage_dir(self):
		try:
			return getattr(settings, 'IMAGE_STORAGE_DIR')
		except AttributeError:
			return settings.MEDIA_ROOT


	def delete_image(self, hash):
		os.unlink(os.path.join(self.get_storage_dir(), hash))


	def save_image(self, hash, filename):
		shutil.copyfile(filename, os.path.join(self.get_storage_dir(), hash))


	def get_image_url(self, hash):
		# XXX check for a setting
		prefix = settings.IMAGE_PATH_PREFIX if 'IMAGE_PATH_PREFIX' in settings else ''
		return settings.MEDIA_URL + prefix + "/" + hash


	def get_required_settings(self):
		return []


class SCPImageStorage(ImageStorage):
	def identity_file_str(self):
		try:
			return "-i " + settings.SSH_IDENTITY_FILE
		except AttributeError:
			return ""

	def delete_image(self, hash):
		os.system("ssh %(identify_file)s %(ssh_user)s \"rm %(file_path)s\"" % {
					'identity_file': self.identity_file_str(),
					'ssh_user': settings.SSH_MEDIA_USER,
					'file_path': os.path.join(settings.SSH_MEDIA_PATH, hash)})

	def save_image(self, filename):
		os.system("scp %(identity_file)s %(filename)s %(ssh_user)s:%(file_path)s" % {
					'identity_file': self.identity_file_str(),
					'ssh_user': settings.SSH_MEDIA_USER, 
					'filename': filename,
					'file_path': os.path.join(settings.SSH_MEDIA_PATH, hash)})

	def get_image_url(self, hash):
		url = settings.PROCESSED_MEDIA_URL
		if url.endswith("/"):
			return url + hash
		else:
			return url + '/' + hash

	def get_required_settings(self):
		return ['PROCESSED_MEDIA_URL', 'SSH_MEDIA_USER', 'SSH_MEDIA_PATH',]

