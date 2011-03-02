"""

Django URL-imaging

Author: Patrick Carroll <patrick@patrickomatic.com>
Version: 0.1

"""
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

from urlimaging.backends.default import *

VERSION = 0.1

# set up the storage backend - default to S3
try:
	settings.IMAGE_STORAGE = eval('%s()' % getattr(settings, 'IMAGE_STORAGE_BACKEND'))
except AttributeError:
	settings.IMAGE_STORAGE = S3ImageStorage()

# depending on the backend used, make sure that all required settings are supplied
for setting in settings.IMAGE_STORAGE.get_required_settings():
	try:
		getattr(settings, setting)
	except AttributeError:
		raise ImproperlyConfigured("You must set %s in your settings.py" % setting)
	

# the function which decides whether or not to process the image
try:
	getattr(settings, 'IMAGE_WHITELIST_FN')
except AttributeError:
	settings.IMAGE_WHITELIST_FN = lambda url: settings.MEDIA_URL in url


# the font settings for watermarking
try:
	getattr(settings, 'FONT_PATH')
except AttributeError:
	settings.FONT_PATH = '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf'

