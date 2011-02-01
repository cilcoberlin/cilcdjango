
from django import forms

from cilcdjango.languages.models import ISOLanguage

class MultipleBasicLanguagesField(forms.ModelMultipleChoiceField):
	"""A multiple-choice select field for basic languages."""

	def __init__(self, *args, **kwargs):
		"""Create the field using a basic languages queryset."""
		kwargs['queryset'] = ISOLanguage.objects.basic()
		super(MultipleBasicLanguagesField, self).__init__(*args, **kwargs)
