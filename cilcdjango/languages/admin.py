
from django.contrib import admin

from cilcdjango.languages.models import ISOLanguage

class ISOLanguageAdmin(admin.ModelAdmin):
	"""Custom admin for ISO 639-3 languages."""

	list_display  = ["iso639_3", "iso639_2_bibliographic", "iso639_2_terminology", "iso639_1", "ref_name", "print_name", "inverted_name"]
	list_filter   = ('type','scope')
	ordering      = ('iso639_3',)
	search_fields = ['print_name', 'inverted_name', 'ref_name']

admin.site.register(ISOLanguage, ISOLanguageAdmin)
