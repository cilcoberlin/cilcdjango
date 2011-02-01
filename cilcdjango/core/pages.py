
from django import forms
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string

import os

class DjangoPage(object):
	"""
	A base class representing a page that can be displayed to a user in a Django
	app that can encapsulate functionality to be used across similar views.

	Pages descended from this class can provide a value for the
	`template_folder` attribute, which will be a path, relative to the templates
	directory, in which any templates rendered by this page reside. For example,
	if you had a page that was to be used to render multiple different views in
	the "TEMPLATE_FOLDER/your_app/sub_dir" directory, it could define
	`template_folder` to be "your_app/sub_dir".

	This class is used in views as follows:

	>>> page = DjangoPage(request)
	>>> page.add_render_args({'your_arg': 'arg_val'})
	>>> return page.render('path_to/your_template')

	"""

	template_folder = None

	def __init__(self, request, *args, **kwargs):
		"""Requires the Request instance as its first argument."""

		self.request     = request
		self._render_args = {}
		self._configure_page(*args, **kwargs)

	def _configure_page(self, *args, **kwargs):
		"""This function can be overridden to perform additional setup actions."""
		pass

	def add_render_args(self, render_args):
		"""Add arguments that are passed to the render_to_response function"""
		self._render_args.update(render_args)

	def _provide_final_render_args(self):
		"""Add rendering arguments right before rendering."""
		return {}

	def _combine_form_media(self):
		"""Combine the media used by all forms in the render arguments."""
		all_media = forms.Media()
		for render_arg in self._render_args.values():
			if hasattr(render_arg, 'media'):
				all_media += render_arg.media
		return all_media

	def resolve_template_path(self, template_name):
		"""
		Return the expanded path to the template passed as `template_name`,
		prepending the current pages `template_folder` and providing a default
		".html" extension if no extension is specified in `template_name`.
		"""

		#  Assume an HTML template, unless an extension is provided
		if template_name.endswith(".html"):
			template_path = template_name
		else:
			template_path = "%s.html" % template_name

		#  Add on the page's template folder if the path isn't absolute or
		#  doesn't already begin with the page's template folder prefix
		if self.template_folder and not template_path.startswith(self.template_folder) and not os.path.isabs(template_path):
			template_path = os.path.join(self.template_folder, template_path)

		return template_path

	def render(self, template_name, to_string=False):
		"""
		Return markup for the page, using the assembled rendering arguments and
		the template path provided in `template_name`.

		If the `to_string` keyword argument is False, the page is returned as an
		HttpResponse instance. If it is True, it is returned as a string.
		"""

		#  Assemble CSS body classes and JavaScript and CSS media files
		self.add_render_args(self._provide_final_render_args())
		self.add_render_args({
			'page_media': self._combine_form_media()
		})

		#  Return either an HTTP response object or a simple string, based on
		#  the requested rendering type
		render_function = render_to_string if to_string else render_to_response
		return render_function(self.resolve_template_path(template_name),
							   self._render_args,
							   context_instance=RequestContext(self.request))
