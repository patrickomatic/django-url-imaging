.. image:: http://pledgie.com/campaigns/14384.png?skin_name=chrome
    :alt: Click here to lend your support to: django-url-imaging and make a donation at www.pledgie.com!
    :target: http://www.pledgie.com/campaigns/14384


django-url-imaging
==================

django-url-imaging provides URL-based image processing functionality for Django
projects.  It features a plugabble storage system with implementations for
storing images locally,  on `Amazon S3`_ or using the SCP utiltiy to copy them
to another server.  


Overview
--------

Once installed and configured, django-url-imaging will allow you to embed
thumbnails and other image transformations using nothing more than a specially
crafted URL.  As an example, if you configured django-url-imaging to listen
for requests on ``/thumbnails/`` and needed to have a resized copy of the 
image at ``http://media.mydomain.com/foo.jpg``, you would just create a link
like: ::

  <img src="/thumbnails/resize/50x50/media.mydomain.com/foo.jpg" />

django-url-imaging provides many different URL-based commands_ for image
processing such as cropping, resizing, scaling, watermarking and `much more`_.
For more information on django-url-imaging, please check out the Wiki_.


Installation
------------

1. Download_ and install django-url-imaging using Distutils_:

  ``$ sudo python setup.py install``

2. Add the ``urlimaging`` app to ``INSTALLED_APPS``

3. Include ``urlimaging.urls`` as a resource in your ``urls.py``:

  ``(r'thumbnails/', include('urlimaging.urls')),``

4. Finally, depending on if you want to use S3 or local file storage, configure the appropriate settings:


Configuration
-------------

Depending on how you plan to store your images, you will need to add one of the
following sets of properties to your ``settings.py`` file:

Amazon S3
~~~~~~~~~

* ``IMAGE_STORAGE_BACKEND`` – This should be set to 'S3ImageStorage' to specify the S3 storage backend.

* ``S3_BUCKET_NAME`` – The name of the bucket (which should already be created) on S3 where images will be stored.

* ``AWS_ACCESS_KEY_ID`` – The AWS access key provided by Amazon.

* ``AWS_SECRET_ACCESS_KEY`` – The AWS secret access key provided by Amazon.

* ``S3_EXPIRES`` (optional) – The length of time which the S3-generated URL will be valid.



Local Image Storage
~~~~~~~~~~~~~~~~~~~

* ``IMAGE_STORAGE_BACKEND`` – This parameter should be set to 'LocalImageStorage' for the local image storage backend.

* ``IMAGE_WHITELIST_FN`` – A function which takes a url as an argument and uses that to decide whether or not to allow it to be processed.  By default it is defined as ``lambda url: True`` which will allow for processing all images.  To restrict it to only process images in your ``MEDIA_URL``, set it to:

  IMAGE_WHITELIST_FN = lambda url: settings.MEDIA_URL in url

* ``IMAGE_STORAGE_DIR`` (optional) – The full path to the directory where images should be stored if this is not set, the value is inherited from MEDIA_ROOT. This directory should be publicly accessible since the application doesn't serve images directly from it.


SCP
~~~

If you'd like to use the ``scp`` command to copy the generated files to another UNIX-like server, configure the following options:

* ``PROCESSED_MEDIA_URL`` - A URL where the images can be accessed once they are stored

* ``SSH_MEDIA_USER`` - The username which has ssh access on the remote host

* ``SSH_MEDIA_PATH`` - The path to where the images will be stored on the remote host

* ``SSH_IDENTITY_FILE`` - If an identity file is required for access to the remote host, this is the path to that file.



Additional Configuration
------------------------

* ``MEDIA_URL`` – If you're using the LocalImageStorage backend, setting this parameter gives the root url that serves images stored in the ``IMAGE_STORAGE_DIR``

* ``FONT_PATH`` - The path to the font file to be used when using the watermark operation.  Defaults to ``/usr/share/fonts/truetype/freefont/FreeSansBold.ttf``



.. _Amazon S3: http://google.com
.. _Download: http://github.com/patrickomatic/django-url-imaging/downloads
.. _Distutils: http://docs.python.org/distutils/
.. _configure: http://wiki.github.com/patrickomatic/django-url-imaging/installation
.. _commands: http://wiki.github.com/patrickomatic/django-url-imaging/how-to-use
.. _much more: http://wiki.github.com/patrickomatic/django-url-imaging/how-to-use
.. _Wiki: http://wiki.github.com/patrickomatic/django-url-imaging/
