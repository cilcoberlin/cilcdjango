
from django import template

register = template.Library()

@register.inclusion_tag('media_forms/selection_form.html')
def media_selection_form(media_form):
	"""Render the media selection form."""
	return {
		'form': media_form,
		'library': media_form.library
	}
