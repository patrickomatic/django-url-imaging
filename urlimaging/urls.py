try:
    from django.conf.urls.defaults import patterns, urls
except ImportError:
    # newer versions of django have switched to this location
    from django.conf.urls import patterns, url

from urlimaging.views import modify

urlpatterns = patterns('',
		url(r'^(.*)$', modify),
)
