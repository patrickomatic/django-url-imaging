from django.conf import settings

from urlimaging.backends.default import S3ImageStorage


__all__ = ['ImageStorage', 'S3ImageStorage', 'LocalImageStorage']
