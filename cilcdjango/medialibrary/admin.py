
from django.contrib import admin

from cilcdjango.medialibrary.models import MediaItem

class MediaItemAdmin(admin.ModelAdmin):
	"""Custom admin for media library items."""

	list_display  = ["file", "url", "title", "library", "type"]
	list_filter   = ('type','library', 'file', 'url')
	ordering      = ('title',)
	search_fields = ['title', 'url', 'file']

admin.site.register(MediaItem, MediaItemAdmin)
