#!/usr/bin/env python

from distutils.core import setup

setup(
		name="django-url-imaging",
		version="0.3.2",
		description="URL-based image processing for Django",
		author="Patrick Carroll",
		author_email="patrick@patrickomatic.com",
		requires=['boto', 'PIL', 'django'],
		url="https://github.com/patrickomatic/django-url-imaging",
		packages=['urlimaging', 'urlimaging.backends'],
)

