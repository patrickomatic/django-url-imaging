#!/usr/bin/env python

from distutils.core import setup

setup(
		name="django-url-imaging",
		version="0.3",
		description="URL-based image processing for Django",
		author="Patrick Carroll",
		author_email="patrick@patrickomatic.com",
		requires=['boto', 'PIL', 'django'],
		url="http://urlimg.com/opensource",
		packages=['urlimaging', 'urlimaging.backends'],
)

