"""

Django URL-imaging

Author: Patrick Carroll <patrick@patrickomatic.com>
Version: 0.1

"""

from django.conf import settings
from urlimaging.backends.default import S3ImageStorage

settings.IMAGE_STORAGE = S3ImageStorage()


VERSION = 0.1
