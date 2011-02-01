
from django import forms
from django.utils.translation import ugettext_lazy as _

from cilcdjango.core.fields import YesNoField
from cilcdjango.core.forms import DjangoForm, DjangoModelForm
from cilcdjango.core.media import SharedMediaMixin
from cilcdjango.medialibrary.models import MediaLibraryGroup, MediaItem

import copy

class MediaLibraryForm(DjangoForm, SharedMediaMixin):
	"""
	The selection form for the media library which.

	Through client-side Ajax, this can also display the media addition form.
	"""

	_FILTER_COLUMN_SIZE = 10
	_GROUP_EMPTY_LABEL = _("all groups")
	_MEDIA_TYPE_CHOICES = [('any', _('any type')), ('files', _('files')), ('urls', _('urls'))]
	_SUBTYPE_DEFAULT_CHOICE = [('any', _("any subtype"))]

	def __init__(self, library, *args, **kwargs):
		"""Requires a MediaLibrary instance as its first argument."""

		super(MediaLibraryForm, self).__init__(*args, **kwargs)
		self.library = library

		widget_args = {
			'attrs': {'size': 10}
		}

		#  Add the group filter
		self.fields['group_filter'] = forms.ModelChoiceField(
			empty_label=self._GROUP_EMPTY_LABEL,
			queryset=library.groups.all().order_by('name'),
			widget=forms.Select(**widget_args),
			required=False,
			initial=""
		)

		#  Add the type filter for choosing files or URLs
		self.fields['type_filter'] = forms.ChoiceField(
			choices=self._MEDIA_TYPE_CHOICES,
			widget=forms.Select(**widget_args),
			required=False,
			initial='any'
		)

		#  Add filters for a subtype of the selected media type
		self.fields['subtype_filter'] = forms.ChoiceField(
			choices=self._make_subtype_filter_choices(library.all_media_types()),
			widget=forms.Select(**widget_args),
			required=False,
			initial='any'
		)

		#  Add the file list
		self.fields['file_list'] = forms.ModelChoiceField(
			queryset=library.media.order_by('title'),
			widget=forms.Select(**widget_args),
			required=False
		)

		#  Remove any POST data with a null value, which is used by
		#  ModelChoiceFields to indicate that no value was selected
		data = self.data.copy()
		for key, value in data.iteritems():
			if value == 'null':
				del data[key]
		self.data = data

	def _make_subtype_filter_choices(self, subtypes):
		"""
		Transform a QuerySet of media types into an iterable suitable to pass as
		the `choices` kwarg of a selection field.
		"""
		return self._SUBTYPE_DEFAULT_CHOICE + [(s.name, s.name) for s in subtypes]

	def clean(self):
		"""Apply the requested filters to the media available in this library."""

		#  Use the requested filters to generate choices for each of the filters
		type_filter = self.cleaned_data.get('type_filter')
		if type_filter == "any":
			local_filter = None
		elif type_filter == "files":
			local_filter = True
		else:
			local_filter = False

		subtype_filter = self.cleaned_data.get('subtype_filter')
		if subtype_filter == "any":
			subtype_filter = None

		filtered = self.library.filter_media(
			local=local_filter,
			media_type=subtype_filter,
			group=self.cleaned_data.get('group_filter', None)
		)

		#  Update the subtypes and media list with the the filtered data
		self.fields['file_list'].queryset = filtered['media']
		self.fields['subtype_filter'].choices = self._make_subtype_filter_choices(filtered['types'])

		return self.cleaned_data

	class SharedMedia:

		js = (
			'core/js/libs/jquery/jquery.simplemodal.js',
			'core/js/libs/jquery/jquery.form.js',
			'medialibrary/js/library.js'
		)

class AddMediaGroupForm(DjangoModelForm):
	"""A form for adding a media group."""

	class ErrorText:
		name = _("you must provide a group name")

	class Meta:
		model = MediaLibraryGroup
		exclude = ('media',)

	def __init__(self, library, *args, **kwargs):
		"""Requires a MediaLibrary instance as its first argument."""

		super(AddMediaGroupForm, self).__init__(*args, **kwargs)
		self.library = library

class AddMediaForm(DjangoModelForm):
	"""A form for adding media to a media library."""

	is_file = YesNoField(label=_("media type"), initial=True, yes=_("file"), no=_("url"))
	new_group_name = forms.CharField(label=_("group name"), required=False)

	class ErrorText:

		title = _("you must provide a title")

	class Meta:
		model = MediaItem
		exclude = ('type',)

	def __init__(self, library, *args, **kwargs):
		"""Requires a MediaLibrary instance as the first argument."""

		super(AddMediaForm, self).__init__(*args, **kwargs)
		self.library = library

		group_args = {
			'queryset': MediaLibraryGroup.objects.filter(library=library).order_by('name'),
			'required': False
		}

		#  Add a group selection form for the media library's groups
		self.fields['groups'] = forms.ModelMultipleChoiceField(label=_("groups"), **group_args)

	def clean(self):
		"""
		Verify that the media type that has been specified is paired with a
		valid medium of the selected type.
		"""

		#  Verify that the user is submitting a medium of the chosen type
		is_file = self.cleaned_data.get('is_file', None)
		if is_file:
			if not self.cleaned_data.get('file'):
				raise forms.ValidationError(_("you must provide a file"))
		elif is_file is not None:
			if not self.cleaned_data.get('url'):
				raise forms.ValidationError(_("you must provide a URL"))
		else:
			raise forms.ValidationError(_("you must select an upload type"))

		#  Remove any cleaned data on non-selected media
		try:
			if is_file:
				del self.cleaned_data['url']
			else:
				del self.cleaned_data['file']
		except KeyError:
			pass

		return self.cleaned_data

	def save(self, *args, **kwargs):
		"""
		Link the medium to any requested media groups after it has committed to
		the database.
		"""

		#  Add the medium to each selected group
		medium = super(AddMediaForm, self).save(*args, **kwargs)
		for group in self.cleaned_data['groups']:
			group.media.add(medium)
		return medium
