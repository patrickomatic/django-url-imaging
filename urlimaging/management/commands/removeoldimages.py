import datetime
from django.conf import settings
from django.core.management.base import NoArgsCommand

from urlimaging.models import ModifiedImage


class Command(NoArgsCommand):
	help = "Remove all images from the database that haven't been checked for 2 days"

	def handle_noargs(self, **options):
		week_ago = datetime.datetime.now() - datetime.timedelta(days=settings.IMAGE_EXPIRATION_DAYS)
		for img in ModifiedImage.objects.filter(last_checked__lte=week_ago):
			img.delete()
