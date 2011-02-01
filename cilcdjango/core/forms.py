
from django import forms
from django.forms.models import BaseModelFormSet
from django.forms.util import ErrorList
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

import re

#-------------------------------------------------------------------------------
#  Form Objects
#-------------------------------------------------------------------------------

class _FieldRenderer(object):
	"""
	A utility class used to render a field on a form descended from the
	_DjangoFormMixin class.  This field render is used in templates by calling
	{{ FORM_NAME.field.FIELD_NAME }}.
	"""

	class CSSClasses:
		"""CSS class names used for the rendered markup."""

		errors     = "has-error"
		field      = "form-field"
		help_text  = "help-text"
		inputs     = "inputs"
		label      = "field-label"
		labels     = "field-labels"
		must_break = "must-break"
		not_used   = "not-used"
		required   = "required"

	def __init__(self, form):
		self._form = form
		self._error_shown = False
		self._field_classes = {}

	def __getitem__(self, name):
		"""Return the field indicated by `name`'s markup."""
		return self.render_field(name)

	def add_field_classes(self, field, classes):
		"""Add classes to a field."""
		if field not in self._field_classes:
			self._field_classes[field] = list(classes)
		else:
			self._field_classes[field].extend(classes)

	def remove_field_classes(self, field, classes):
		"""Remove classes from a field."""
		if field in self._field_classes:
			for klass in classes:
				try:
					index = self._field_classes[field].index(klass)
				except ValueError:
					pass
				else:
					self._field_classes[field] = self._field_classes[field][:index] + self._field_classes[field][index+1:]

	def render_field(self, field):
		"""Return HTML markup to render the requested field."""

		form_field = self._form[field]

		#  Customize the field's CSS classes
		classes = [self.CSSClasses.field]
		if form_field.errors:
			classes.append(self.CSSClasses.errors)
		if getattr(form_field.field, 'not_used', False):
			classes.append(self.CSSClasses.not_used)
		if form_field.field.required:
			classes.append(self.CSSClasses.required)
		if getattr(form_field.field, 'must_break', False):
			classes.append(self.CSSClasses.must_break)
		if hasattr(form_field.field, 'field_classes'):
			classes.extend(form_field.field.field_classes)

		#  Add any custom field classes specified by the form
		classes.extend(self._field_classes.get(field, []))

		#  Build a class for the field container that takes the auto_id into
		#  account, removes an initial id_ prefix, and transforms any
		#  underscores into hyphens
		field_name = form_field.html_name
		if self._form.auto_id:
			try:
				field_name = re.sub(r'^id_', '', self._form.auto_id) % field_name
			except TypeError:
				pass
		field_name = field_name.replace('_', '-')

		#  Build the beginning markup
		form_markup = ["<div class='%s' id='%s-%s'>" % (" ".join(classes), self.CSSClasses.field, field_name)]
		if form_field.errors:
			form_markup.append(force_unicode(form_field.errors))
		form_markup.append("<p class='%s'>" % self.CSSClasses.labels)

		#  Get the label as a string, either from a proxy object or a unicode string
		old_label = label_text = force_unicode(form_field.label)

		#  Title-case the label text, avoiding apparent acronyms, unless it
		#  seems to have formatting of some sort already in it, as indicated by
		#  a capitalized first letter.
		if not re.search(r'^[A-Z]', label_text):
			new_label = []
			for l_part in re.split(r'\s+', label_text):
				new_label.append(l_part.title() if not re.search(r'^[A-Z]{2,}', l_part) else l_part)
			label_text = " ".join(new_label)
		label_tag = form_field.label_tag(attrs={'class': self.CSSClasses.label})
		if old_label != label_text:
			label_tag = re.sub(r'>(\s+)?%s' % old_label, r'>%s' % label_text, label_tag)
		form_markup.append(label_tag)

		if form_field.help_text:
			form_markup.append(form_field.label_tag(contents=form_field.help_text.capitalize(), attrs={'class': self.CSSClasses.help_text}))
		form_markup.append("</p><div class=\"%s\">" % self.CSSClasses.inputs)
		form_markup.append(force_unicode(form_field))
		form_markup.append("</div></div>")

		return mark_safe("\n".join(form_markup))

class _DjangoFormMixin(object):
	"""
	A mixin used to give additional functionality to a Django form.

	A form using this mixin has a few additional features. First, each field can
	be rendered using more verbose markup than normal by calling {{
	FORM_NAME.field.FIELD_NAME }} in a template. It also accepts three custom
	classes that can be defined for the form, which are discussed below.

	The first custom class is `ReplaceField`, whose attribute names are the name
	of a field defined on the form, and whose value is a new instance of a form
	field.

	The second custom class is `ErrorText`, whose attribute names are the name
	of a field defined on the form, and whose value, if a string, will be the
	error text shown if a required field is not filled in. The value can also be
	a dict whose keys are the name of the error to show text for, and whose
	value will be that error text.

	The third custom class is `FieldClasses`, whose attributes are the names of
	fields defined on the form and whose values are iterables containing the
	names of classes to be applied to the field's container.
	"""

	@property
	def ajax_errors(self):
		"""The value of the first error associated with the form."""
		try:
			for e_name, e_vals  in self._errors.iteritems():
				return e_vals[0]
		except IndexError:
			pass
		return _("a form error occurred")

	def get_instance(self):
		"""Return an instance only if the current form's instance has been saved."""
		return self.instance if self.instance.pk else None

	def _new_or_old_field_value(self, value, field, new_field):
		"""
		Get either the value specified in `value` on the replacement field class
		given in `new_field` or use the current value for the field given in
		`field`.
		"""
		return getattr(new_field, value) or getattr(field, value)

	def add_field_classes(self, field, classes):
		"""Proxy to the field renderer's field class addition method."""
		self.field.add_field_classes(field, classes)

	def remove_field_classes(self, field, classes):
		"""Proxy to the field renderer's field class removal method."""
		self.field.remove_field_classes(field, classes)

	def replace_field(self, field_name, new_field, keep_values=False):
		"""
		Replace a form field, preserving the label and help text of the
		original, unless these values are specified in the replacement field, of
		if `keep_values` is set to True.
		"""

		try:
			field = self.fields[field_name]
		except (AttributeError, KeyError):
			return None

		#  Take a snapshot of the pre-replacement field values
		if not keep_values:
			old_help     = self._new_or_old_field_value('help_text', field, new_field)
			old_initial  = self._new_or_old_field_value('initial', field, new_field)
			old_label    = self._new_or_old_field_value('label', field, new_field)
			old_required = self._new_or_old_field_value('required', field, new_field)
			old_errors   = field.error_messages

		self.fields[field_name] = new_field

		#  Update the field's attributes
		if not keep_values:
			self.fields[field_name].help_text      = old_help
			self.fields[field_name].initial        = old_initial
			self.fields[field_name].label          = old_label
			self.fields[field_name].required       = old_required
			self.fields[field_name].error_messages = old_errors

	def add_error(self, field_name, error_text):
		"""Add an error to the error list for the field named `field_name`."""
		error_text = force_unicode(error_text)
		if field_name in self._errors:
			self._errors[field_name].append(error_text)
		else:
			self._errors[field_name] = ErrorList([error_text])

	def check_bool(self, field):
		"""
		Returns the value of the checkbox or boolean radio value named `field`,
		giving priority to POST data, if it exists, and then falling back to the
		bound model instance.
		"""
		if self.data:
			return form_bool(self.data.get(field))
		else:
			return getattr(self.instance, field)

class DjangoForm(forms.Form, _DjangoFormMixin):
	"""Base class for a non-model Django form."""

	def __init__(self, *args, **kwargs):
		super(DjangoForm, self).__init__(*args, **kwargs)
		self.field = _FieldRenderer(self)
		_initialize_custom_form(self)

class DjangoModelForm(forms.ModelForm, _DjangoFormMixin):
	"""Base class for a Django form linked to a model."""

	def __init__(self, *args, **kwargs):
		super(DjangoModelForm, self).__init__(*args, **kwargs)
		self.field = _FieldRenderer(self)
		_initialize_custom_form(self)

#-------------------------------------------------------------------------------
#  Formset Objects
#-------------------------------------------------------------------------------

class ModelMultipleChoiceResponseFormset(BaseModelFormSet):
	"""A formset for handling possible responses to multiple choice questions."""

	def add_fields(self, form, index):
		"""Make each field value not required, to allow for formset-wide validation."""

		super(ModelMultipleChoiceResponseFormset, self).add_fields(form, index)
		for field in form.fields:
			form.fields[field].required = False

#-------------------------------------------------------------------------------
#  Helper Functions
#-------------------------------------------------------------------------------

def form_bool(value):
	"""
	Return the value of a form as a Boolean value, making sure that 'False' is
	rendered as the False boolean type.
	"""
	if value and value.lower() == 'false':
		return False
	else:
		return bool(value)

def _get_properties(obj):
	"""
	Return a tuple of the property / value pairs of a class's variables,
	ignoring any __ variables.
	"""
	return [(prop, val) for prop, val in obj.__dict__.iteritems() if not prop.startswith("__")]

def _initialize_custom_form(new_form):
	"""
	Initialize the form passed in `new_form`, which should harness the
	_DjangoFormMixin mixin, using custom classes defined on the form to perform
	the initialization and customization.
	"""

	#  Replace any fields specified with their replacements. The original values
	#  of the field, derived from the model, will be preserved unless explicitly
	#  specified in the field creation call.
	if hasattr(new_form, 'ReplaceFields'):
		for field, replace_with in _get_properties(new_form.ReplaceFields):
			new_form.replace_field(field, replace_with)

	#  Apply the error text to each field. This text is contained in and
	#  ErrorText class, which will have class variables that can either be full
	#  dictionaries keyed by the type of error raised, or a shorthand string,
	#  which will map to the 'required' error key.
	if hasattr(new_form, 'ErrorText'):
		for field, messages in _get_properties(new_form.ErrorText):
			try:
				messages = {'required': messages.strip()}
			except AttributeError:
				pass
			try:
				new_form.fields[field].error_messages.update(messages)
			except (AttributeError, KeyError):
				pass

	#  Set any custom field classes, which are contained in the FieldClasses
	#  class on the form, which will have class variables matching the name of a
	#  field, and a value of an iterable containing class names
	if hasattr(new_form, 'FieldClasses'):
		for field, classes in _get_properties(new_form.FieldClasses):
			new_form.add_field_classes(field, classes)
