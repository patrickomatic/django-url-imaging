import sys, unicodedata
from django.http import Http404, HttpResponseRedirect
from django.conf import settings

from urlimaging.models import *


def modify(request, url):
	if request.META['QUERY_STRING']:
		url = url + "?" + request.META['QUERY_STRING']

	cr = CommandRunner(url)

	if not settings.IMAGE_WHITELIST_FN(cr.url):
		raise Http404	

	try:
		if not cr.todo: 
			print >>sys.stderr, "Unable to parse url: %s" % url
			raise Http404
		
		img = cr.run_commands()
		if not img: 
			print >>sys.stderr, "Unable to run commands: %s" % url
			raise Http404

		return HttpResponseRedirect(img)
	except ImageNotFoundException:
		raise Http404
	
	raise Http404
