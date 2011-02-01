
from cilcdjango.core.users import LDAPConnection

from django.contrib.auth.models import User

import ldap

class AuthenticationBase(object):
	"""Authentication base that implements the required get_user function."""

	def get_user(self, user_id):
		"""Return a Django user if one exists with the ID given in `user_id`."""
		try:
			return User.objects.get(pk=user_id)
		except User.DoesNotExist:
			return None

class LDAPBackend(AuthenticationBase):
	"""Validates users against Oberlin's LDAP."""

	def authenticate(self, username=None, password=None):
		"""
		Check for a user's existence in LDAP, creating a local Django User model
		for the user if they do not already have one.
		"""

		user = None

		#  Connect to the Oberlin server, binding as the user
		try:
			ldap_conn = LDAPConnection(user_id=username, user_password=password)
		except ldap.LDAPError:
			return None
		else:
			user_info = ldap_conn.get_info_from_obie_id(username)

		#  If the user exists in LDAP, get a current record of them in Django's
		#  auth system, or add a new user using the LDAP information, allowing
		#  a descended class to interact with each step of the creation
		if user_info is not None:

			try:
				user = User.objects.get(username=username)
			except User.DoesNotExist:

				#  Get user information from LDAP
				create_info = {
					'last_name':  user_info['last_name'],
					'first_name': user_info['first_name'],
					'email':      user_info['email']
				}
				create_info.update(self.provide_additional_user_creation_info(user_info, create_info))

				#  Create the user with a random password
				random_pwd = User.objects.make_random_password(20)
				user = User(username=username, password=random_pwd, **create_info)

				#  Get their professor status
				user.is_staff = user_info['professor']
				user.save()

				#  Allow child classes to perform further configuration on the new user
				self.do_post_user_creation_config(user, user_info, random_pwd)

			#  Allow a child class to perform further action on the user
			self.do_post_validation_actions(user, user_info)

		return user

	def provide_additional_user_creation_info(self, user_info, create_info):
		"""
		Return a dict containing additional keyword arguments to be passed when
		creating a new User instance.

		This can be overridden by a child authentication class if it needs to
		customize the creation of the User instance. The `user_info` arg is a
		dict of values obtained from LDAP, and `create_info` is the current dict
		of parameters that will be passed to the new User model.
		"""
		return {}

	def do_post_user_creation_config(self, user, user_info, default_password):
		"""
		Perform post-creation customization to a newly created User instance.

		This can be overridden by a child authentication class that needs to
		alter the User instance after it has been created. The `user` arg
		contains the new User instance, `user_info` is a dict of values obtained
		from LDAP, and `default_password` is the current password assigned to
		the user.
		"""
		pass

	def do_post_validation_actions(self, user, user_info):
		"""Perform actions after the user has been validated against LDAP."""
		pass
