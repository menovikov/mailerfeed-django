from math import ceil

import django.contrib.auth.password_validation as validators
from django.core.exceptions import ValidationError

import phonenumbers


def validate_pass(pass1, pass2):
	errors = []
	if pass1 != pass2:
		errors.append("Пароли различаются")
	try:
		validators.validate_password(pass1)
	except ValidationError as e:
		errors.extend(e)
	return errors

def validate_phone(phone):
	try:
		return phonenumbers.is_valid_number(phonenumbers.parse(phone, 'RU'))
	except:
		return False

def validate_int(num):
	try:
		int(num)
		return True
	except (ValueError, TypeError):
		return False

def paginator(page, start, end, step, items_count):
	page_max = ceil(items_count / step)
	page1 = page2 = page3 = None
	if page == -1:
		page = page_max
	if page >= page_max:
		page3 = page_max
		page2 = page3 - 1 if (page3 - 1) >= 1 else None
		page1 = page2 - 1 if page2 and (page2 - 1) >= 1 else None
	elif page > 0 and page <= page_max and page != 1:
		page1 = page - 1 if (page - 1) > 0 else None
		page2 = page
		page3 = page + 1 if (page + 1) <= page_max else None
	elif page == 1:
		page1 = page
		page2 = page1 + 1 if (page1 + 1) <= page_max else None
		page3 = page2 + 1 if page2 and (page2 + 2) <= page_max else None

	if page > 1 and page <= page_max:
		start = step * (page - 1)
		end = start + step
	return start, end, {'page1': page1, 'page2': page2, 'page3': page3}

