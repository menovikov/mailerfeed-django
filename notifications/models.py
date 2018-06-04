from django.contrib.auth.models import User
from django.db import models


class BaseNotification(models.Model):

	NONE = 0
	DEBUG = 1
	INFO = 2
	WARNING = 3
	ERROR = 4
	CRITICAL = 5
	LEVELS = (
		(NONE, "No notification"),
		(DEBUG, "Debug"),
		(INFO, "Info"),
		(WARNING, "Warning"),
		(ERROR, "Error"),
		(CRITICAL, "Critical"),
	)

	USERS_BLUE = "fa fa-users text-aqua"
	USERS_RED = "fa fa-users text-red"
	SHOPPING_CART_GREEN = "fa fa-shopping-cart text-green"
	WARNING_YELLOW = "fa fa-warning text-yellow"
	USER_RED = "fa fa-user text-red"
	CSS_CLASSES = (
		(USERS_BLUE, USERS_BLUE),
		(USERS_RED, USERS_RED),
		(SHOPPING_CART_GREEN, SHOPPING_CART_GREEN),
		(WARNING_YELLOW, WARNING_YELLOW),
		(USER_RED, USER_RED),
	)

	title = models.CharField(max_length=128)
	level = models.CharField(max_length=25, choices=LEVELS, default=INFO)
	user = models.ForeignKey(User)
	created = models.DateTimeField(auto_now=True)
	css_class = models.CharField(max_length=128, choices=CSS_CLASSES, default=WARNING_YELLOW)

	class Meta:
		abstract = True
		ordering = ('-created',)


class WebNotification(BaseNotification):
	pass

