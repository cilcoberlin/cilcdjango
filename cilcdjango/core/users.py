
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

import ldap
from ldap.filter import escape_filter_chars
import re

_LDAP_DEFAULTS = {
	'LDAP_PROTOCOL':      ldap.VERSION3,
	'LDAP_SCOPE':         ldap.SCOPE_SUBTREE,
	'LDAP_SERVER':        "ldaps://ldap1.cc.oberlin.edu",
	'LDAP_SEARCH_BASE':   "ou=people,o=oberlin.edu,o=oberlin-college",
	'LDAP_USER_DN':       None,
	'LDAP_USER_PASSWORD': None
}

#  This uses the default LDAP settings as a base, but replaces any value
#  whose key occurs as a variable in the Django project's settings.py file
#  with the value found in the project settings.
ldap_settings = {}
for setting, value in _LDAP_DEFAULTS.iteritems():
	ldap_settings[setting] = getattr(settings, setting, value)

class LDAPConnection():
	"""
	A wrapper class for interacting with an LDAP connection that allows a user
	to make LDAP queries and view information on the returned user or users as
	dicts.

	This class is intended to be used as follows:

	>>> conn = LDAPConnection()
	>>> user = conn.get_info_from_obie_id('jdoe')
	>>> print user
	{
		'user_id':    'jdoe',
		'last_name':  'John',
		'first_name': 'Doe',
		'email':      'john.doe@oberlin.edu',
		't_number':   'T12345678',
		'professor':   False
	}

	"""

	#  The values are the names of the information as it appears in LDAP, and
	#  the keys are the names that will be used internally to refer to the values
	desired_attributes = {
		'user_id':    'uid',
		'last_name':  'sn',
		'first_name': 'givenName',
		'email':      'mail',
		't_number':   'OberlinTNumber',
		'professor':  'o'
	}

	def __init__(self, user_id=None, user_password=None):
		"""
		Initialize a connection to the LDAP server, using the provided user
		information if possible, otherwise defaulting to the application user.
		"""

		self._ldap_user_info = None
		self._ldap_conn      = None

		#  Use the user information provided or the application user
		if user_id is None or user_password is None:
			user_dn  = ldap_settings['LDAP_USER_DN']
			password = ldap_settings['LDAP_USER_PASSWORD']
		else:
			user_dn  = "uid=%s,%s" % (user_id, ldap_settings['LDAP_SEARCH_BASE'])
			password = user_password

		#  Connect to the Oberlin LDAP server
		self._ldap_conn = ldap.initialize(ldap_settings['LDAP_SERVER'])
		self._ldap_conn.protocol_version = ldap_settings['LDAP_PROTOCOL']
		self._ldap_conn.simple_bind_s(user_dn, password)

	def get_info_from_obie_id(self, uid):
		"""
		Return a dict containing information on a user with the Obie ID provided
		as `uid`.
		"""
		return self._make_ldap_query({'uid': uid})

	def get_info_from_tnumber(self, t_number):
		"""
		Return a dict containing information on a user identified by the T
		number passed as `t_number`.
		"""
		return self._make_ldap_query({'OberlinTNumber': t_number})

	def _make_ldap_query(self, query_args, unique=True):
		"""
		Execute an LDAP query for a user who matches the filter parameters
		provided in the `query_args` dict, where each key is the name of a valid
		LDAP field, and each value is the value requested for that field.

		The results of this query will be returned as dict whose keys will match
		those defined in the `desired_attributes` class attribute.

		If the `unique` keyword argument is True and more than one record is
		returned, an error will be raised.
		"""

		#  Build our filter string
		filters = "".join([ "(%s=%s)" % (key, escape_filter_chars(val)) for key, val in query_args.iteritems() ])
		if len(query_args) > 1:
			filters = "(&%s)" % filters

		#  The LDAP results object is of the form [0 => user DN, 1 => user info]
		results = self._ldap_conn.search_st(ldap_settings['LDAP_SEARCH_BASE'], ldap_settings['LDAP_SCOPE'], filters)
		if results:
			if unique and len(results) > 1:
				raise ValueError(_("expected a unique record, but %(record_count)d records were found!") % {
					'record_count': len(user_info)
				})

			#  Map the LDAP values to our requested attributes
			info_list = []
			for result in [result[1] for result in results]:
				user_info = {}
				for dict_key, ldap_val in self.desired_attributes.iteritems():
					user_val = result.get(ldap_val)
					try:
						user_val = user_val.pop()
					except AttributeError:
						pass
					user_info[dict_key] = user_val
				user_info['professor'] = user_info.get('professor', [""]) == "Faculty"
				info_list.append(user_info)

			return info_list.pop() if unique else info_list

		return None
