django-url-imaging
==================

django-url-imaging provides URL-based image processing functionality for Django
projects.  It features a plugabble storage system with implementations for
storing images locally or on `Amazon S3`_.  

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

#. Download_ and install django-url-imaging using Distutils_

#. Add the ``urlimaging`` app to ``INSTALLED_APPS``

#. Include ``urlimaging.urls`` as a resource in your ``urls.py``

#. Finally, depending on if you want to use S3 or local file storage, configure_ the appropriate settings.

.. _Amazon S3: http://google.com
.. _Download: http://github.com/patrickomatic/django-url-imaging/downloads
.. _Distutils: http://docs.python.org/distutils/
.. _configure: http://wiki.github.com/patrickomatic/django-url-imaging/installation
.. _commands: http://wiki.github.com/patrickomatic/django-url-imaging/how-to-use
.. _much more: http://wiki.github.com/patrickomatic/django-url-imaging/how-to-use
.. _Wiki: http://wiki.github.com/patrickomatic/django-url-imaging/
