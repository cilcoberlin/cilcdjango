
import cilcdjango.core.settings as _settings
from cilcdjango.core.url import site_url
from cilcdjango.core.util import get_app_setting

from django.core.urlresolvers import reverse, NoReverseMatch
from django.utils.safestring import mark_safe

import simplejson as json

class CILCContext(object):
	"""
	Base class for a context that makes information about the current
	application available to templates.

	By default, this context provides the following variables:

	    GOOGLE_ANALYTICS - Markup for having Google Analytics track a page
	    MEDIA_URL        - The absolute URL to the app's media directory
	    REQUEST_PATH     - The request path used to get to the current page
	    SHARED_MEDIA_URL - The absolute URL to the app's shared media directory
	    SITE_URL         - The absolute URL to the application's root directory

	To add additional context variables, a child context class can override
	the `provide_context_variables` function, which should return a dictionary
	whose keys will be the names of template variables.

	This context also provides a special variable named "JS_GLOBAL_VARIABLES"
	that contains markup to define JavaScript global variables.

	Three separate global JavaScript objects are defined that contain settings.
	The first, `cilc`, acts as a simple namespace for CILC apps. The second,
	`cilc_settings`, defines URLs and information about the current application.
	The last, `custom_js_settings` (although the value can be changed if the
	child class ovverrides the value of `js_globals_object`),
	contains any variables provided by the child context via an overridden
	`provide_javascript_globals` method, whose returned dictionary's keys will
	be the names of global variables available through the `custom_js_settings`
	object.
	"""

	_JS_GLOBALS_OBJECT_NAME  = "cilc"
	_JS_SETTINGS_OBJECT_NAME = "cilc_settings"
	_JS_GLOBALS_URL_VAR_NAME = "urls"
	_JS_GLOBALS_CONTEXT_NAME = "JS_GLOBAL_VARIABLES"

	js_globals_object = "custom_js_settings"

	def __init__(self, request):
		from django.conf import settings
		self.request          = request
		self.app_root         = get_app_setting('APP_ROOT_FOLDER')
		self.shared_media_url = get_app_setting('SHARED_MEDIA_URL')
		self.app_media_url    = settings.MEDIA_URL
		self.url_config       = settings.ROOT_URLCONF

	def _build_javascript_globals(self):
		"""Provide certain settings and paths as JavaScript globals."""

		self._js_vars = {
			'widgets': {}
		}

		self._js_settings_vars = {
			'app_name':         get_app_setting('APPLICATION_NAME'),
			'app_root':         self.app_root,
			'media_url':        self.app_media_url,
			'shared_media_url': self.shared_media_url
		}

	def _add_ajax_view_to_java_script(self, pattern):
		"""
		Make an AJAX view decorated by the `ajax_view` decorator available via
		its name to a JavaScript object that is a property of the custom
		settings object.
		"""

		#  If the pattern can be resolved without any args or kwargs, implying
		#  that it receives its data via POST, add it to our list.
		if hasattr(pattern.callback, _settings.AJAX_VIEW_FLAG):
			try:
				self._custom_js_vars[self._JS_GLOBALS_URL_VAR_NAME][pattern.name] = reverse(pattern.name)
			except NoReverseMatch:
				pass

	def _add_ajax_views_to_java_script(self, patterns):
		"""
		Add any URL patterns used by the current application to the JavaScript
		custom globals object.
		"""

		#  Add an individual pattern if possible, and otherwise recurse to add
		#  any included groups of URLs.
		for pattern in patterns:
			if hasattr(pattern, 'url_patterns'):
				self._add_ajax_views_to_java_script(pattern.url_patterns)
			else:
				self._add_ajax_view_to_java_script(pattern)

	def _render_java_script_globals(self):
		"""Render the markup that defines the JavaScript global variables."""

		global_markup = ["<script type='text/javascript'>"]

		#  Add any available AJAX view URLs to the custom settings object.
		try:
			exec("from %s import urlpatterns" % self.url_config)
		except ImportError:
			pass
		else:

			#  Make sure that a URL dict exists for the settings object
			if self._JS_GLOBALS_URL_VAR_NAME not in self._custom_js_vars:
				self._custom_js_vars[self._JS_GLOBALS_URL_VAR_NAME] = {}

			#  Add any AJAX views to our object
			self._add_ajax_views_to_java_script(urlpatterns)

		#  A list of JavaScript values and the variable names they should have
		object_list = [
			{
				'object':   self._js_vars,
				'var_name': self._JS_GLOBALS_OBJECT_NAME
			},
			{
				'object':   self._js_settings_vars,
				'var_name': self._JS_SETTINGS_OBJECT_NAME
			},
			{
				'object':   self._custom_js_vars,
				'var_name': self.js_globals_object
			}
		]

		#  Add core and user-added variables by serializing the Python data as JSON
		var_markup = []
		for js_vars in object_list:
			if js_vars['object']:
				var_markup.append("%s = %s" % (js_vars['var_name'], json.dumps(js_vars['object'])))
		global_markup.append("var %s;" % ",".join(var_markup))

		global_markup.append("</script>")
		return mark_safe("\n".join(global_markup))

	def _build_google_analytics_code(self):
		"""
		Create the JavaScript code to enable Google Analytics tracking for the
		page, using a settings value to get the account ID.
		"""

		ga_id   = get_app_setting("GOOGLE_ANALYTICS_ID")
		markup = ""

		if ga_id:
			script_blocks = (
				(
					"var ga_js_host = ((\"https:\" == document.location.protocol) ? \"https://ssl.\" : \"http://www.\");",
					"document.write(unescape(\"%3Cscript src='\" + ga_js_host + \"google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E\"));"
				),
				(
					"try {",
					"var page_tracker = _gat._get_tracker(\"%s\");" % ga_id,
					"page_tracker._track_pageview();",
					"} catch(err) {}"
				)
			)
			markup = "\n".join([
				"<script type=\"text/javascript\">%s</script>" % "".join(block) for block in script_blocks
			])

		return mark_safe(markup)

	def provide_context_variables(self):
		"""
		Add variables to the template context.

		This can be overridden by a child class that wishes to add additional
		variables to the template context. Each key in the returned dictionary
		will be the name of the variable.
		"""
		return {}

	def provide_java_script_globals(self):
		"""
		Add global JavaScript variables.

		This can be overridden by a child context to provide additional
		JavaScript global variables that will be contained in the
		`js_globals_object` object, which is "custom_js_settings"
		by default.
		"""
		return {}

	def build_context(self):
		"""Create a dict of context variables that can be used in templates."""

		# Add paths to the site and its media
		if self.request.is_secure():
			self.app_media_url = self.app_media_url.replace('http:', 'https:')
			self.shared_media_url = self.shared_media_url.replace('http:', 'https:')
		paths = {
			'GOOGLE_ANALYTICS': self._build_google_analytics_code(),
			'MEDIA_URL':        self.app_media_url,
			'REQUEST_PATH':     self.request.path,
			'SHARED_MEDIA_URL': self.shared_media_url,
			'SITE_URL':         site_url()
		}

		#  Allows child classes to add context variables
		paths.update(self.provide_context_variables())

		#  Add in our JavaScript global variables
		self._build_javascript_globals()
		self._custom_js_vars = self.provide_java_script_globals()
		paths[self._JS_GLOBALS_CONTEXT_NAME] = self._render_java_script_globals()

		return paths
