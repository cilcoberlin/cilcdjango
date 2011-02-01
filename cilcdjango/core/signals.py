
def ensure_unique_defaults(default_field="default", with_fields=[], deleting=False, **kwargs):
	"""
	Verify that the value of `default_field` on the current model is True only
	once across the field specified in the `with_fields` kwarg.

	If this is already the case, nothing happens. If the current instance is set
	as the default, all other instances are marked as not the default. If the
	instance is being and it is the default, the first other instance of the
	model is set as the default.
	"""

	#  Abort if the fields specified don't actually exist
	sender   = kwargs.get('sender')
	instance = kwargs.get('instance')
	for attr in [default_field] + [field for field in with_fields]:
		if not hasattr(instance, attr):
			return

	#  Build the set for which the default should be unique that includes the instance
	unique_subset = sender.objects.all()
	for field in with_fields:
		unique_subset = unique_subset.filter(**{field: getattr(instance, field)})

	#  If there are other items, make sure that only one of them is the default.  If
	#  the current instance has been marked as the default, make it the default, and
	#  set the other records to not be the defaults.  If no records are the default,
	#  make the first record added be the default.
	if unique_subset.count() > 1:
		other_uniques = unique_subset.filter(**{default_field: True}).exclude(pk=instance.pk)
		if other_uniques.count() > 0:
			if getattr(instance, default_field) is True and not deleting:
				for other_unique in other_uniques:
					setattr(other_unique, default_field, False)
					other_unique.save()
		else:
			if bool(getattr(instance, default_field)) is deleting:
				if deleting:
					unique_subset = unique_subset.exclude(pk=instance.pk)
				first_record = unique_subset.order_by('pk')[0]
				setattr(first_record, default_field, True)
				first_record.save()

	#  If there is only one record within the set of records that should be
	#  uniquely default, make sure that it is marked as the default, regardless
	#  of user input, provided that the record is not being removed.
	else:
		if getattr(instance, default_field) is False and not deleting:
			setattr(instance, default_field, True)
			instance.save()
