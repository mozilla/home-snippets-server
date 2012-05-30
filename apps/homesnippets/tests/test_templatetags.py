from collections import namedtuple

from django.conf import settings
from django.template import Context
from django.template.loader import get_template_from_string
from django.test import TestCase

from nose.tools import eq_

class TestICanHaz(TestCase):
    """Test the icanhaz template tag."""

    def setUp(self):
        """Create empty context to render test templates with."""
        self.context = Context()

    def test_basic(self):
        """Tests icanhaz bracket replacement."""
        template_str = """
        {% load icanhaz %}
        {% icanhaz %}
          Nyan [Nyan] [[Nyan]] [[[Nyan]]]
        {% endicanhaz %}
        """
        template = get_template_from_string(template_str)
        result = template.render(self.context).strip()

        eq_(result, 'Nyan [Nyan] {{Nyan}} {{{Nyan}}}',
            "Single brackets should' be preserved, but double and triple "
            "brackets should be replaced.")


class TestGetAttribute(TestCase):
    def setUp(self):
        """Create empty context to render test templates with."""
        self.context = Context()

    def test_basic(self):
        """Test if getattribute can retrieve an object attribute."""
        Point = namedtuple('Point', ['x', 'y'])
        self.context['p'] = Point(4, 5)

        template_str = """
        {% load getattribute %}
        {{ p|getattribute:'x' }}
        """
        template = get_template_from_string(template_str)
        result = template.render(self.context).strip()

        eq_(result, '4')

    def test_nonexistant_attribute_returns_invalid(self):
        """
        If the requested attribute doesn't exist, return the invalid template
        string.
        """
        Point = namedtuple('Point', ['x', 'y'])
        self.context['p'] = Point(4, 5)

        template_str = """
        {% load getattribute %}
        {{ p|getattribute:'q' }}
        """
        template = get_template_from_string(template_str)
        result = template.render(self.context).strip()

        eq_(result, settings.TEMPLATE_STRING_IF_INVALID)
