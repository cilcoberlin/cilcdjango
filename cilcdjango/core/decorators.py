
from cilcdjango.core.exceptions import AjaxError
from cilcdjango.core.http import JsonResponse
import cilcdjango.core.settings as _settings
from cilcdjango.core.util import get_app_setting

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.encoding import force_unicode

from functools import wraps
import inspect
import re

#-------------------------------------------------------------------------------
#  View Helpers
#-------------------------------------------------------------------------------

def ajax_view(view_function):
	"""
	Wrapper for Ajax views that handles shared logic.

	This can be applied to an Ajax view. This view may and generally will return
	a dictionary whose values define a JSON response, which will be packaged
	into an actual JSON response by this decorator. If the decorated view
	instead returns a standard HttpResponse instance, then that is returned with
	no further processing.

	In addition to this logic, this decorator also maps values contained in the
	POST data to any keyword arguments in the decorated function. It attempts to
	convert the normally string-only POST values to types matching the types of
	the default values provided for the keyword argument. For example, the view
	function `my_view(a, b=2, c=True)` would populate "b" with the value of
	int(request.POST['b']) and "c" with the value of bool(request.POST['c']).
	"""

	#  Determine which function args are keyword arguments, based upon
	#  getargspec returning a tuple with four values, where the first is the
	#  list of function arguments and the last is a list of any default values.
	arg_spec     = inspect.getargspec(view_function)
	base_args    = arg_spec[0]
	kw_defaults  = arg_spec[3]
	base_kw_args = base_args[0-len(kw_defaults):] if kw_defaults else []

	def ajax_view(request, *args, **kwargs):

		#  Get the response object from our function, as it will always be the
		#  first positional argument, and search its POST data for values
		#  matching the name of any of the decorated function's keyword args,
		#  applying these to the kwargs for the function, while attempting to
		#  convert the type of the POST value to match the default for the kwarg.
		new_args = {}
		non_arg_data = request.POST.copy()
		for key, value in request.POST.iteritems():
			if key in base_kw_args:

				#  Since a bool value will make both bool("0") and bool("1")
				#  be true, if we have a boolean kwarg, try to convert the
				#  value to an int first
				if type(kw_defaults[base_kw_args.index(key)]) == bool:
					try:
						value = int(value)
					except ValueError:
						pass

				#  Perform the actual value casting. If we succeed, remove the
				#  current value from the POST data, so that it does not
				#  interfere with forms created in the Ajax view
				try:
					key_name = str(key)
					new_args[key_name] = kw_defaults[base_kw_args.index(key)].__class__(value)
				except ValueError:
					pass
				else:
					del non_arg_data[key_name]
		kwargs.update(new_args)
		request.POST = non_arg_data

		#  Get our view response and handle exceptions if we're debugging
		view_success = True
		error_message = u""
		i_frame = False
		try:
			response_data = view_function(request, *args, **kwargs)
		except AjaxError, e:
			view_success = False
			error_message = force_unicode(e.message)
			response_data = {'error': error_message.capitalize()}
			i_frame = e.i_frame
			if settings.DEBUG:
				print error_message
		except Exception, e:
			if settings.DEBUG:
				print e
				response_data = {}
				view_success = False
			else:
				raise e

		#  If it's a standard HTTP response, render that
		if hasattr(response_data, 'status_code'):
			return response_data

		#  Or make it a JSON response, adding in our predetermined success value
		#  and a possible error text obtained from a caught AjaxError
		else:
			response_data['success'] = view_success
			return JsonResponse(response_data, i_frame=i_frame)

	#  Flag the Ajax view as such, for the sake of other cilcdjango functions
	setattr(ajax_view, _settings.AJAX_VIEW_FLAG, True)
	return wraps(view_function)(ajax_view)

def dynamic_js(view_function):
	"""
	Wrapper that makes a view that returns JavaScript code provide an
	appropriate MIME type.
	"""
	def new_view(*args, **kwargs):
		return HttpResponse(view_function(*args, **kwargs), mimetype='text/javascript')
	return new_view

def requires_secure(view_function):
	"""
	Ensure than an HTTPS connection is made for the view if one can be.

	This tries to strip any port information from the URL and change the
	protocol to HTTPS, converting a URL like http://sub.main.tld:80/app/ to
	https://sub.main.tld/app/.
	"""

	def new_view(*args, **kwargs):

		#  If the current application supports secure connections, strip any
		#  port information and change the protocol on the URL.
		request = args[0]
		if not request.is_secure() and get_app_setting('SUPPORTS_HTTPS'):
			return HttpResponseRedirect(
				re.sub(r'\:\d+\/', r'/', request.build_absolute_uri().replace('http://', 'https://')))
		else:
			return view_function(*args, **kwargs)

	return new_view
