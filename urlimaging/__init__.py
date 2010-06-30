"""

Django URL-imaging

Author: Patrick Carroll <patrick@patrickomatic.com>
Version: 0.1

"""
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

from urlimaging.backends.default import *

# Python 2.7 has an importlib with import_module; for older Pythons,
# Django's bundled copy provides it.
try:
	from importlib import import_module
except ImportError:
	from django.utils.importlib import import_module

VERSION = 0.1

# set up the storage backend - default to S3
try:
	settings.IMAGE_STORAGE = import_module(getattr(settings, 'IMAGE_STORAGE_BACKEND'))
except AttributeError:
	settings.IMAGE_STORAGE = S3ImageStorage()

for setting in settings.IMAGE_STORAGE.get_required_settings():
	try:
		getattr(settings, setting)
	except AttributeError:
		raise ImproperlyConfigured("You must set %s in your settings.py" % setting)
	
try:
	getattr(settings, 'IMAGE_WHITELIST_FN')
except AttributeError:
	settings.IMAGE_WHITELIST_FN = lambda url: settings.MEDIA_URL in url
