
from cilcdjango.core.media import make_shared_media_url, make_secure_media_url
from cilcdjango.core.forms import DjangoForm, DjangoModelForm
import cilcdjango.core.text
from cilcdjango.core.util import get_app_setting, rfc3339_to_datetime

from django import template
from django.conf import settings
from django.template.defaultfilters import date, stringfilter
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _, ugettext

import datetime
import lxml.html
import os
import re

register = template.Library()

#-------------------------------------------------------------------------------
#  Email Tags
#-------------------------------------------------------------------------------

@register.simple_tag
def email_support():
	"""Return a link to email the support address specified in the settings."""
	return mark_safe(u'<a href="mailto:%s">%s</a>' % (
		get_app_setting('SUPPORT_EMAIL_ADDRESS'),
		get_app_setting('SUPPORT_EMAIL_NAME')
	))

#-------------------------------------------------------------------------------
#  URL Filters
#-------------------------------------------------------------------------------

@stringfilter
@register.filter
def break_cache(url):
	"""Append the current datetime to the URL to prevent it from being cached."""
	return "%(url)s?%(datetime)s" % {
		'url': url,
		'datetime': "".join(
			str(ord(c)) for c in datetime.datetime.now().isoformat()
		)
	}

#-------------------------------------------------------------------------------
#  Formatting Filters
#-------------------------------------------------------------------------------

@stringfilter
@register.filter
def smart_title(value):
	"""Titlecase the text in `value`, trying to preserve formatted text."""
	return mark_safe(cilcdjango.core.text.smart_title(value))

@stringfilter
@register.filter
def line_breaks_p(value):
	"""
	Transform any apparent paragraphs, as indicated by blocks of text separated
	by line breaks, into paragraphs marked with <p> tags.
	"""
	return mark_safe(re.sub(r'\n', '</p><p>', u"<p>%s</p>" % re.sub(r'\n+', '\n', value).strip()))

@stringfilter
@register.filter
def highlight(value, arg):
	"""
	Wrap any occurrences of the string `arg` in the whitespace-separated
	components of the string `value` in emphasizing markup.
	"""
	for part in re.split(r'\s+', arg):
		sub = re.compile(r'([^>]{0,1})(%s)([^<]{0,1})' % part, re.I)
		value = sub.sub(r'\1<strong class="highlight">\2</strong>\3', value)
	return mark_safe(value)

#-------------------------------------------------------------------------------
#  Formatting Tags
#-------------------------------------------------------------------------------

@register.filter
@stringfilter
def rfc3339_date(date_string, date_filter):
	"""
	A version of Django's `date` filter that works on datetime strings formatted
	according to the RFC 3339 guidelines and can accept an optional `X`
	parameter that displays the timezone name as produced by using the `X`
	parameter in python's strftime function.
	"""
	dt = rfc3339_to_datetime(date_string)
	if dt.tzinfo and 'X' in date_filter:
		date_filter = date_filter.replace('X', "".join(["\%s" % letter for letter in dt.strftime("%Z")]))
	formatted = date(dt, date_filter)
	return formatted

@register.tag
def form_field(parser, token):
	"""
	When called as {% form_field form field classes %}, where `classes` is
	optional, return the markup for the requested field on the given form with
	the optional classes added to its existing classes.
	"""
	try:
		tag_name, form_name, field_name, classes = token.split_contents()
	except ValueError:
		try:
			tag_name, form_name, field_name = token.split_contents()
		except ValueError:
			raise template.TemplateSyntaxError(ugettext("the form_field tag requires a form instance and then a field name"))
		else:
			classes = u""
	classes = re.split(r'\s+', re.sub(r'["\']', '', classes))
	return FormFieldNode(form_name, field_name, classes)

class FormFieldNode(template.Node):
	"""Renderer for the `form_field` tag."""

	def __init__(self, form_name, field_name, classes):
		self._form_name = template.Variable(form_name)
		self._field_name = field_name
		self._classes = classes

	def render(self, context):
		"""Return markup defining the form's field."""

		#  Make sure that the form inherits from one of the cilcdjango form
		#  classes and is a valid form instance
		try:
			form = self._form_name.resolve(context)
		except template.VariableDoesNotExist:
			raise template.TemplateSyntaxError(
				ugettext("the first argument to the form_field tag must be a form instance"))
		if not issubclass(form.__class__, DjangoForm) and not issubclass(form.__class__, DjangoModelForm):
			raise template.TemplateSyntaxError(
				ugettext("the form passed to the form_field tag must be a subclass of DjangoForm or DjangoModelForm"))

		form.add_field_classes(self._field_name, self._classes)
		markup = form.field.render_field(self._field_name)
		form.remove_field_classes(self._field_name, self._classes)
		return markup

@register.tag
def strip_ws(parser, token):
	"""Strip whitespace from the beginning and end of a string."""
	nodelist = parser.parse(('endstrip_ws',))
	parser.delete_first_token()
	return StripWSNode(nodelist)

class StripWSNode(template.Node):
	"""Renderer for the `strip_ws` tag."""

	def __init__(self, nodelist):
		self.nodelist = nodelist

	def render(self, context):
		output = self.nodelist.render(context)
		return output.strip()

@register.tag
def remove_empty_attr(parser, token):
	"""Remove an attribute from a tag if its value is blank."""
	nodelist = parser.parse(('endremove_empty_attr',))
	parser.delete_first_token()
	return EmptyAttributeNode(nodelist)

class EmptyAttributeNode(template.Node):
	"""Renderer for the `remote_empty_attr` tag."""

	_is_empty_tag = re.compile(r'\w+\=["\']{2}')

	def __init__(self, nodelist):
		self.nodelist = nodelist

	def render(self, context):
		output = self.nodelist.render(context)
		tag_base = output.strip().replace(" ", "")
		return "" if self._is_empty_tag.search(tag_base) else output

@register.tag
def remove_empty_tag(parser, token):
	"""Remove a tag if it contains nothing but whitespace."""

	nodelist = parser.parse(('endremove_empty_tag',))
	parser.delete_first_token()
	return EmptyTagNode(nodelist)

class EmptyTagNode(template.Node):
	"""Renderer for the `remove_tempty_tag` tag."""

	_ignore_empty_tags = set([
		'br',
		'hr'
	])

	def __init__(self, nodelist):
		"""
		Initialize the nodelist and a list of empty tags that we wish to count
		as valid tags.
		"""
		self.nodelist = nodelist
		self.empty_tags = lxml.html.defs.empty_tags - self._ignore_empty_tags

	def render(self, context):
		"""Return the tag's markup if it is not empty, or nothing if it is."""
		output = self.nodelist.render(context)
		root = lxml.html.fragment_fromstring(output)
		if all([
			not tag.text_content().strip() and tag.tag not in self.empty_tags
			for tag in root.iter()]):
			return u""
		return output

#-------------------------------------------------------------------------------
#  Media Tags
#-------------------------------------------------------------------------------

def _is_quoted(value):
	"""
	Return True if the string in `value` is surrounded by matching double or
	single quotes.
	"""
	return (value[0] == value[-1] and value[0] in ('"', "'"))

def _parse_css_token(token):
	"""
	Parse an `add_css` tag, which takes two arguments, being the absolute or
	relative path to the CSS file and a string of the media types for which the
	stylesheet should be displayed
	"""
	try:
		tag_name, file_path, media_types = token.split_contents()
	except ValueError:
		raise template.TemplateSyntaxError(ugettext("the css tag requires two arguments, the path to a media file and the media types"))
	if not _is_quoted(file_path) or not _is_quoted(media_types):
		raise template.TemplateSyntaxError(ugettext("the %(tag)r tag's arguments should be in quotes") % {'tag': tag_name})
	return (file_path, media_types)

def _parse_js_token(token):
	"""
	Parse an `add_js` tag, which takes a single argument of the relative or
	absolute path to the JavaScript file.
	"""
	try:
		tag_name, file_path = token.split_contents()
	except ValueError:
		raise template.TemplateSyntaxError(ugettext("the javascript tag requires one argument, the path to a media file"))
	if not _is_quoted(file_path):
		raise template.TemplateSyntaxError(ugettext("the %(tag)r tag's argument should be in quotes") % {'tag': tag_name})
	return file_path

def _parse_media_token(token):
	"""
	Parse an add media tag, which takes a single argument of an instance of a
	Django form Media object.
	"""
	try:
		tag_name, media_instance = token.split_contents()
	except ValueError:
		raise template.TemplateSyntaxError(ugettext("the media tag requires one argument, a Django Media instance"))
	return media_instance

@register.tag
def add_css(parser, token):
	"""Include a CSS file in a template."""
	file_path, media_types = _parse_css_token(token)
	return AddCSSNode(file_path, media_types, False)

@register.tag
def add_shared_css(parser, token):
	"""Include a shared CSS file in a template."""
	file_path, media_types = _parse_css_token(token)
	return AddCSSNode(file_path, media_types, True)

@register.tag
def add_js(parser, token):
	"""Include a JavaScript file in a template."""
	return AddJavaScriptNode(_parse_js_token(token), False)

@register.tag
def add_shared_js(parser, token):
	"""Include a shared JavaScript file in a template."""
	return AddJavaScriptNode(_parse_js_token(token), True)

@register.tag
def add_media_js(parser, token):
	"""Include the JavaScript contained in a Django Media instance in a template."""
	return AddMediaCollectionNode(_parse_media_token(token), js=True)

@register.tag
def add_media_css(parser, token):
	"""Include the CSS contained in a Django Media instance in a template."""
	return AddMediaCollectionNode(_parse_media_token(token), css=True)

class AddMediaCollectionNode(template.Node):
	"""
	A node that renders media contained in a Django Media instance.

	This takes one required argument and two optional ones. The required
	argument is a reference to a Media instance. The optional arguments are the
	`js` or `css` keyword arguments. If `js` is True, then the JavaScript in the
	Media instance will be included, and if `css` is True, the same thing will
	happen for the CSS contained in the Media instance.
	"""

	def __init__(self, media_instance, js=False, css=False):
		self.media_instance = template.Variable(media_instance)
		self.js = js
		self.css = css

	def render(self, context):
		"""Render markup to include each file that is part of the Media instance."""

		try:
			media_instance = self.media_instance.resolve(context)
		except template.VariableDoesNotExist:
			return ""

		#  If the Media instance has media for the requested type, create a
		#  rendering node for each of the files and add it to the markup
		media_type = "js" if self.js else "css"
		media = getattr(media_instance, '_%s' % media_type, None)
		if media:
			markup = []
			if self.js:
				for js_file in media:
					markup.append(AddJavaScriptNode(js_file, False).render(context))
			elif self.css:
				for medium in media:
					for css_file in media[medium]:
						markup.append(AddCSSNode(css_file, medium, False).render(context))
			return mark_safe("\n".join(markup))
		else:
			return ""

class AddMediaNode(template.Node):
	"""Base class for any media addition nodes."""

	def __init__(self, file_path, shared):
		self.shared = shared
		self.file_path = self._un_quote(file_path)

	def _un_quote(self, value):
		"""Unquote a value"""
		return re.sub(r'["\']', '', value)

	def _normalize_file(self, request):
		"""
		Normalize the file path managed by this node, making it an absolute URL
		referencing the shared media URL if it's shared or pointing to the
		current project's media URL if not. Furthermore, if the tag was able to
		access the `request` object from the context, make it secure if the
		request itself is secure.
		"""
		if self.shared:
			self.file_path = make_shared_media_url(self.file_path)
		else:
			if not self.file_path.startswith("http"):
				self.file_path = os.path.join(settings.MEDIA_URL, self.file_path)
		if request is not None and request.is_secure():
			self.file_path = make_secure_media_url(self.file_path)

	def render(self, context):
		"""
		Return markup to include the the media only if it has yet to be included
		by a previous tag.
		"""

		self._normalize_file(context.get('request', None))
		markup = mark_safe(self.add_media())

		#  Create a render context to keep track of loaded media for Django 1.2
		#  or greater, which adds the render_context
		if hasattr(context, 'render_context'):
			if 'loaded_media' not in context.render_context:
				context.render_context['loaded_media'] = []
			loaded_media = context.render_context['loaded_media']

			#  Only add the file if it has yet to be loaded by another tag
			if self.file_path not in loaded_media:
				loaded_media.append(self.file_path)
				return markup
			else:
				return ""

		#  If the version of Django doesn't have a render_context, just return
		#  the media insertion markup
		else:
			return markup

	def add_media(self):
		"""
		Create the actual output to add the media.

		This must be implemented by a child Node class.
		"""
		raise NotImplementedError

class AddCSSNode(AddMediaNode):
	"""A node that includes a CSS file via a <link> to an external stylesheet."""

	IS_IE_SHEET = re.compile(r'ie\.(?P<condition>\w{2,3})?\.?(?P<version>\d+(\.\d+)?)?\.?css$')

	def __init__(self, file_path, media_types, shared):

		super(AddCSSNode, self).__init__(file_path, shared)
		self.media_types = self._un_quote(media_types)

	def _process_ie_stylesheets(self, base_markup):
		"""
		Wrap conditional CSS meant only for IE in conditional comments.

		These comments are generated from the file's naming conventions. If a
		file is called "ie.lt.8.css", for example, it will be wrapped in a
		conditional comment making it visible to IE version 8 or less.
		"ie.7.css" will only show for IE version 7, and "ie.css" will display
		for any version of IE.
		"""

		markup = [base_markup]

		#  Wrap the stylesheet markup in conditional IE comments if needed
		match = self.IS_IE_SHEET.search(self.file_path)
		if match:
			version   = match.group('version')
			condition = match.group('condition')
			comment = ["<!--[if"]
			if condition:
				comment.append(condition)
			comment.append("IE")
			if version:
				comment.append(version)
			comment.append("]>")
			markup.insert(0, " ".join(comment))
			markup.append("<![endif]-->")

		return "\n".join(markup)

	def add_media(self):
		"""
		Add the stylesheet as a <link>, possibly wrapping it in IE conditional
		comments, depending on the file name.
		"""
		return self._process_ie_stylesheets('<link href="%s" rel="stylesheet" type="text/css" media="%s" />' % (
			self.file_path, self.media_types
		))

class AddJavaScriptNode(AddMediaNode):
	"""A node that includes an external JavaScript file via a <script> tag."""

	def add_media(self):
		return '<script type="text/javascript" src="%s"></script>' % self.file_path
