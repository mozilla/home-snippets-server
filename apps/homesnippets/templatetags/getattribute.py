from django import template
from django.conf import settings


register = template.Library()


def getattribute(value, arg):
        """Gets an attribute of an object dynamically from a string name"""
        if hasattr(value, str(arg)):
                return getattr(value, arg)
        else:
                return settings.TEMPLATE_STRING_IF_INVALID

register.filter('getattribute', getattribute)
