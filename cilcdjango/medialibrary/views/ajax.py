
from django.http import HttpResponse
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _

from cilcdjango.core.decorators import ajax_view
from cilcdjango.core.exceptions import AjaxError
from cilcdjango.core.http import JsonResponse
from cilcdjango.core.pages import DjangoPage
from cilcdjango.core.shortcuts import get_object_or_ajax_error
from cilcdjango.medialibrary.forms import AddMediaForm, MediaLibraryForm, AddMediaGroupForm
from cilcdjango.medialibrary.models import MediaLibrary, MediaItem
import cilcdjango.medialibrary.settings as _settings

import re
import simplejson as json

def _get_library(library_id):
	"""Return a MediaLibrary instance whose primary key matches `library_id`."""
	return get_object_or_ajax_error(MediaLibrary, pk=library_id)

@ajax_view
def update_filters(request, library_id=0):
	"""Return markup to define the media library filters."""

	library = _get_library(library_id)
	filter_form = MediaLibraryForm(library)

	page = DjangoPage(request)
	page.add_render_args({
		'form': filter_form,
		'library': library
	})

	return {
		'markup': {
			'filters': page.render('media_forms/selection_form_filters.html', to_string=True)
		}
	}

@ajax_view
def filter_media_library(request, library_id=0):
	"""
	Return markup to define the media library selection filters, based upon the
	filters passed in request.POST.
	"""

	library = _get_library(library_id)
	filter_form = MediaLibraryForm(library, request.POST)

	if filter_form.is_valid():
		page = DjangoPage(request)
		page.add_render_args({
			'form': filter_form
		})

		return {
			'markup': {
				'subtypes': page.render('media_forms/selection_form_filter_subtypes.html', to_string=True),
				'media':    page.render('media_forms/selection_form_filter_items.html', to_string=True)
			}
		}
	else:
		raise AjaxError(filter_form.ajax_errors)

@ajax_view
def load_add_media_form(request, library_id=0):
	"""Return markup for the media addition form."""

	library = _get_library(library_id)
	add_form = AddMediaForm(library, auto_id=_settings.ADD_MEDIA_FORM_AUTO_ID)
	new_group_form = AddMediaGroupForm(library, auto_id=_settings.ADD_GROUP_FORM_AUTO_ID)

	#  Return the markup for the media library's addition form
	page = DjangoPage(request)
	page.add_render_args({
		'media_form': add_form,
		'group_form': new_group_form,
		'library': library
	})
	return {
		'markup': {
			'form': page.render('media_forms/add_form.html', to_string=True)
		}
	}

@ajax_view
def add_media_group(request, library_id=0):
	"""
	Add a new media library group and return markup for the updated group
	selector, which will now include the newly added group.
	"""

	library = _get_library(library_id)
	request.POST['library'] = library_id

	#  Create the new media group
	group_form = AddMediaGroupForm(library, request.POST)
	if group_form.is_valid():
		new_group = group_form.save()
	else:
		raise AjaxError(group_form.ajax_errors)

	#  Return the markup for the group selector
	add_form = AddMediaForm(library, auto_id=_settings.ADD_MEDIA_FORM_AUTO_ID)
	page = DjangoPage(request)
	page.add_render_args({'media_form': add_form})
	return {
		'markup': {
			'group_selector': page.render('media_forms/add_form_group_selector.html', to_string=True)
		},
		'message': _("%(group)s added") % {'group': new_group.name}
	}

@ajax_view
def save_add_media_form(request, library_id=0):
	"""Add the user-specified medium to the media library."""

	library = _get_library(library_id)

	add_form = AddMediaForm(library, request.POST, request.FILES)
	if add_form.is_valid():
		medium = add_form.save()
	else:
		raise AjaxError(add_form.ajax_errors, i_frame=request.POST.get('is_file', None) == "True")

	return JsonResponse(
		{
			'message': _("%(medium)s successfully added") % {'medium': medium.title},
			'local': medium.url is None
		},
		i_frame=add_form.cleaned_data['is_file']
	)

@ajax_view
def media_markup(request, media_id=0):
	"""Return the markup needed to render the requested medium."""

	medium = get_object_or_ajax_error(MediaItem, pk=media_id)
	return {
		'markup': {
			'media': re.sub(r'[\n\t]', '', force_unicode(medium.render()))
		}
	}
