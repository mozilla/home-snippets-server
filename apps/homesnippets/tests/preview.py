"""
homesnippets client match rule tests
"""
import logging
import time
import random
import datetime

from django.conf import settings

from django.db import connection

from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client
 
from django.core.cache import cache
from django.core.cache.backends import locmem

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr

from homesnippets.models import Snippet, ClientMatchRule

import homesnippets.models

from homesnippets.tests.utils import HomesnippetsTestCase

class TestSnippetsPreview(HomesnippetsTestCase):

    def test_preview_snippets(self):
        """Exercise the preview-only flag for snippets"""

        rules = self.setup_rules({
            'fields': ( 'startpage_version', 'name', 'version', 'locale', ),
            'items': {
                # Specific rule, expected to be matched
                'specific': ( '1', 'Firefox', '4.0', 'en-US', ),
                # Less-specific rule, should match but not result in duplicate
                'vague': ( '1', 'Firefox', '4.0', None, ),
                # Rule that won't be attached to any snippet.
                'unused': ( '1', 'Mudfish', '7.0', 'en-GB', ),
                # Rule that will be attached to snippet, but not matched.
                'unmatched': ( '2', 'Airdog',  '3.0', 'de' ),
                # Rule matching anything
                'all': ( None, None, None, None ),
            }
        })

        snippets = self.setup_snippets(rules, {
            'fields': ( 'name', 'body', 'preview', 'rules' ),
            'items': {
                # Using specific and less-specific rule
                'preview': ( 'test 1', 'Expected body data', True,
                    ( rules['specific'], rules['vague'] ) ),
                # No rules, so always included in results
                'ever': ( 'test 2', 'Ever-present body data', False,
                    ( rules['all'], ) ),
                # Rule attached that will never be matched, so should never appear
                'never': (' test 3', 'Never-present body data', False,
                    ( rules['unmatched'], ) ),
            }
        })

        self.assert_snippets({
            '/1/Firefox/4.0/xxx/xxx/en-US/xxx/xxx/default/default/': (
                ( snippets['preview'], False  ), 
                ( snippets['ever'], True  ), 
                ( snippets['never'], False ),
            ),
            '/preview/1/Firefox/4.0/xxx/xxx/en-US/xxx/xxx/default/default/': (
                ( snippets['preview'], True  ), 
                ( snippets['ever'], True  ), 
                ( snippets['never'], False ),
            ),
        })
