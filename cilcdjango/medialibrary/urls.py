
from django.conf.urls.defaults import *

urlpatterns = patterns('cilcdjango.medialibrary.views.ajax',

	#  Media library filtering
	url(r'^update_filter/$', 'update_filters', name="update-filters"),
	url(r'^filter/$', 'filter_media_library', name="filter-media-library"),

	#  Media addition form
	url(r'^groups/add/$', 'add_media_group', name='add-media-group'),
	url(r'^forms/add_media/$', 'load_add_media_form', name='load-media-library-add-form'),
	url(r'^forms/add_media/save/$', 'save_add_media_form', name='save-media-library-add-form'),

	#  Media rendering
	url(r'^markup/$', 'media_markup', name="media-markup")
)
