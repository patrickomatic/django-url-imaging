django-url-imaging
==================

django-url-imaging provides URL-based image processing functionality for Django
projects.  It features a plugabble storage system with implementations for
storing images locally or on `Amazon S3`_.  

.. raw:: html
  <a href='http://www.pledgie.com/campaigns/14384'><img alt='Click here to lend your support to: django-url-imaging and make a donation at www.pledgie.com !' src='http://www.pledgie.com/campaigns/14384.png?skin_name=chrome' border='0' /></a>


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

  ``(r'imaging/', include('urlimaging.urls')),``

4. Finally, depending on if you want to use S3 or local file storage, configure the appropriate settings:


Configuration
-------------

Depending on how you plan to store your images, you will need to add one of the
following sets of properties to your ``settings.py`` file:

Amazon S3
~~~~~~~~~

* ``S3_BUCKET_NAME`` – The name of the bucket (which should already be created) on S3 where images will be stored.

* ``S3_EXPIRES`` (optional) – The length of time which the S3-generated URL will be valid.

* ``AWS_ACCESS_KEY_ID`` – The AWS access key provided by Amazon.

* ``AWS_SECRET_ACCESS_KEY`` – The AWS secret access key provided by Amazon.



Local Image Storage
~~~~~~~~~~~~~~~~~~~

* ``S3_BUCKET_NAME`` – The name of the bucket (which should already be created) on S3 where images will be stored.

* ``S3_EXPIRES`` (optional) – The length of time which the S3-generated URL will be valid.

* ``AWS_ACCESS_KEY_ID`` – The AWS access key provided by Amazon.

* ``AWS_SECRET_ACCESS_KEY`` – The AWS secret access key provided by Amazon.


Additional Configuration
------------------------

* ``WHITELIST_FN`` – Defines a function which takes one argument – the URL of the current image processing request. The method should return True or False to either allow the image to be processed or not. If not set it will only allow images to be processed from URLs containing settings.MEDIA_URL

* ``IMAGE_STORAGE_DIRECTORY`` – The directory where temporary image files will be created. Defaults to /tmp


.. _Amazon S3: http://google.com
.. _Download: http://github.com/patrickomatic/django-url-imaging/downloads
.. _Distutils: http://docs.python.org/distutils/
.. _configure: http://wiki.github.com/patrickomatic/django-url-imaging/installation
.. _commands: http://wiki.github.com/patrickomatic/django-url-imaging/how-to-use
.. _much more: http://wiki.github.com/patrickomatic/django-url-imaging/how-to-use
.. _Wiki: http://wiki.github.com/patrickomatic/django-url-imaging/
