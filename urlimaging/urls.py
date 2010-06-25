from django.conf.urls.defaults import *
from urlimaging.image.views import modify

urlpatterns = patterns('',
		url(r'^(.*)$', modify),
)
