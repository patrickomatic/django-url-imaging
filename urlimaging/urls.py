from django.conf.urls.defaults import *
from urlimaging.views import modify

urlpatterns = patterns('',
		url(r'^(.*)$', modify),
)
