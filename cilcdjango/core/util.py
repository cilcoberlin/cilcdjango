
from django.conf import settings
from django.template.defaultfilters import date as django_date
from django.utils.translation import ugettext_lazy as _

import os
import sys

_setting_defaults = {
	'APPLICATION_NAME':      "",
	'APP_ROOT_FOLDER':       "/",
	'RTE_CONFIG_FILE':       "",
	'SERVER_BASE':           None,
	'SERVER_PORT':           80,
	'SHARED_MEDIA_URL':      "",
	'SUPPORTS_HTTPS':        False,
	'SUPPORT_EMAIL_ADDRESS': "",
	'SUPPORT_EMAIL_NAME':    ""
}

TELLTALE_DJANGO_FILES = set(['manage.py', 'settings.py'])

#-------------------------------------------------------------------------------
#  Configuration
#-------------------------------------------------------------------------------

def get_app_setting(setting_name):
	"""
	Try to get the requested setting from the Django project's settings.py file,
	and, failing that, from the default provided in this module.

	Settings for any cilcdjango functionality will have a "CILC_" prefix.
	"""
	return getattr(settings, "CILC_%s" % setting_name, _setting_defaults.get(setting_name, None))

def configure_django_paths(script_path):
	"""
	Add the Django root directory and the current project's directory to
	the path, which is useful when running a Django script from the command line.

	This takes the full path to the invoked script.
	"""

	#  Get the full path to the script's folder
	file_folder = os.path.dirname(os.path.realpath(script_path))

	#  Search for the project directory by looking for key Django files
	project_dir = None
	while not project_dir:
		if os.path.isdir(file_folder):
			if TELLTALE_DJANGO_FILES & set(os.listdir(file_folder)) == TELLTALE_DJANGO_FILES:
				project_dir = file_folder
			else:
				previous_folder = file_folder
				file_folder = os.path.normpath(os.path.join(file_folder, ".."))
				if previous_folder == file_folder:
					raise OSError("Could not find Django project directory")


	#  If we found a project directory, use it to get the Django directory and
	#  the project name, then add these to the path and environment
	if project_dir:
		django_dir, project_name = os.path.split(project_dir)
		sys.path.append(django_dir)
		sys.path.append(project_dir)
		os.environ['DJANGO_SETTINGS_MODULE'] = '%s.settings' % project_name

#-------------------------------------------------------------------------------
#  Date / Time
#-------------------------------------------------------------------------------

def format_date(date_obj):
	"""
	Return the datetime.date instance `date_obj` formatted with the default date
	formatting.
	"""
	return django_date(date_obj, settings.DATE_FORMAT)

def format_datetime(datetime_obj):
	"""
	Return the datetime.datetime instance `datetime_obj` formatted with the
	default datetime formatting.
	"""
	return _("%(date)s at %(time)s") % {
		'date': django_date(datetime_obj, settings.DATE_FORMAT),
		'time': django_date(datetime_obj, settings.TIME_FORMAT)
	}

#-------------------------------------------------------------------------------
#  System
#-------------------------------------------------------------------------------

def import_module(module_path):
	"""Import the module identified by the string `module_path` and return it."""

	#  Return the module directly if it has already been imported, or import it
	#  and then return a reference to it.
	if module_path not in sys.modules:
		__import__(module_path)
	return sys.modules[module_path]
