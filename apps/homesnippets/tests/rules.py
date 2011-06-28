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

class TestSnippetsMatch(HomesnippetsTestCase):
    """Exercise selection of snippets via client match rules"""

    def test_simple_rules(self):
        """Exercise simple exact match rules"""

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
            'fields': ( 'name', 'body', 'rules' ),
            'items': {
                # Using specific and less-specific rule
                'expected': ( 'test 1', 'Expected body data', 
                    ( rules['specific'], rules['vague'] ) ),
                # No rules, so always included in results
                'ever': ( 'test 2', 'Ever-present body data', 
                    ( rules['all'], ) ),
                # Rule attached that will never be matched, so should never appear
                'never': (' test 3', 'Never-present body data', 
                    ( rules['unmatched'], ) ),
            }
        })

        self.assert_snippets({
            '/1/Firefox/4.0/xxx/xxx/en-US/xxx/xxx/default/default/': (
                ( snippets['expected'], True  ), 
                ( snippets['ever'], True  ), 
                ( snippets['never'], False ),
            ),
            '/9/Waterduck/9.2/xxx/xxx/en-US/xxx/xxx/default/default/': (
                ( snippets['expected'], False ), 
                ( snippets['ever'], True  ), 
                ( snippets['never'], False ),
            ),
            '/1/Mudfish/7.0/xxx/xxx/en-GB/xxx/xxx/default/default/': (
                ( snippets['expected'], False ), 
                ( snippets['ever'], True  ), 
                ( snippets['never'], False ),
            ),
        })

    def test_exclusion_rules(self):
        """Exercise match rules that exclude snippets"""

        rules = self.setup_rules({
            'fields': ( 'startpage_version', 'name', 'version', 'locale', 'exclude' ),
            'items': {
                'specific': ( '1', 'Firefox', '4.0', 'en-US', True, ),
                'vague': ( '1', 'Firefox', '4.0', None, False, ),
                'mudfish': ( '1', 'Mudfish', '7.0', 'en-GB', True, ),
                'airdog': ( '2', 'Airdog',  '3.0', 'de', False, ),
                'nowindcat': ( '1', 'Windcat', '9.3', 'fr', True ),
                'all': ( None, None, None, None, False ),
            }
        })

        snippets = self.setup_snippets(rules, {
            'fields': ( 'name', 'body', 'rules' ),
            'items': {
                'en-GB': ( 'test 1', 'Expected in en-GB but not en-US', 
                    ( rules['specific'], rules['vague'] ) ),
                'ever': ( 'test 2', 'Ever-present body data', 
                    ( rules['all'], ) ),
                'never': (' test 3', 'Never-present body data', 
                    ( rules['airdog'], ) ),
                'usually': ( 'test 4', 'Usually-present body data', 
                    ( rules['all'], rules['nowindcat'], ) ),
            }
        })

        self.assert_snippets({
            '/1/Firefox/4.0/xxx/xxx/en-US/xxx/xxx/default/default/': (
                ( snippets['en-GB'], False ), 
                ( snippets['ever'], True  ), 
                ( snippets['never'], False ), 
                ( snippets['usually'], True  ),
            ),
            '/1/Firefox/4.0/xxx/xxx/en-GB/xxx/xxx/default/default/': (
                ( snippets['en-GB'], True  ), 
                ( snippets['ever'], True  ), 
                ( snippets['never'], False ), 
                ( snippets['usually'], True  ),
            ),
            '/1/Windcat/9.3/xxx/xxx/fr/xxx/xxx/default/default/': (
                ( snippets['en-GB'], False ), 
                ( snippets['ever'], True  ), 
                ( snippets['never'], False ), 
                ( snippets['usually'], False ),
            ),
        })

    def test_disabled_snippets(self):
        """Exercise omission of disabled snippets"""

        rules = self.setup_rules({
            'fields': ( 'exclude', ),
            'items': {
                'all': ( False, ),
            }
        })

        snippets = self.setup_snippets(rules, {
            'fields': ( 'name', 'body', 'disabled', 'rules' ),
            'items': {
                'shown_1':  ( 'one',   'Shown 1',  False, ( rules['all'], ) ),
                'disabled': ( 'two',   'Disabled', True,  ( rules['all'], ) ),
                'shown_2':  ( 'three', 'Shown 2',  False, ( rules['all'], ) ),
            }
        })

        self.assert_snippets({
            '/1/Firefox/4.0/xxx/xxx/en-US/xxx/xxx/default/default/': (
                ( snippets['shown_1'],  True ), 
                ( snippets['shown_2'],  True ), 
                ( snippets['disabled'], False ), 
            ),
        })

    def test_pub_start_end_dates(self):
        """Exercise start/end publication dates"""

        rules = self.setup_rules({
            'fields': ( 'exclude', ),
            'items': {
                'all': ( False, ),
            }
        })

        snippets = self.setup_snippets(rules, {
            'fields': ( 'body', 'rules', 'pub_start', 'pub_end', ),
            'items': {
                'shown_1':  ( 'Shown 1', ( rules['all'],),
                    None, 
                    None, ),
                'shown_2':  ( 'Shown 2', ( rules['all'],), 
                    datetime.datetime(2010, 10, 25), 
                    None, ),
                'shown_3':  ( 'Shown 3', ( rules['all'],), 
                    None, 
                    datetime.datetime(2010, 12, 24), ),
                'shown_4':  ( 'Shown 4', ( rules['all'],), 
                    datetime.datetime(2010, 10, 24), 
                    datetime.datetime(2010, 10, 31), ),
            }
        })

        expected = [
            ( datetime.datetime(2010, 10, 01), 
                ( 'shown_1', 'shown_3', ) ),
            ( datetime.datetime(2010, 10, 25), 
                ( 'shown_1', 'shown_2', 'shown_3', 'shown_4', ) ),
            ( datetime.datetime(2010, 12, 24), 
                ( 'shown_1', 'shown_2', 'shown_2', ) ),
            ( datetime.datetime(2011, 01, 01), 
                ( 'shown_1', 'shown_2', ) ),
        ]

        for tm, snippet_names in expected:
            expected_names = set(snippet_names)
            result_names = set(s['name'] 
                for s in Snippet.objects.find_snippets_with_match_rules({}, tm))
            eq_(expected_names, result_names)

    def test_regex_rules(self):
        """Exercise match rules that use regexes"""

        rules = self.setup_rules({
            'fields': ( 'startpage_version', 'name', 'version', 'locale', 'exclude' ),
            'items': {
                'fire_or_mud': ( '1', '/(Firefox|Mudfish)/', '4.0', None, False, ),
                'no_fr_or_de': ( '1', None, '4.0', '/(de|fr)/', True, ),
                'all': ( None, None, None, None, False ),
            }
        })

        snippets = self.setup_snippets(rules, {
            'fields': ( 'name', 'body', 'rules' ),
            'items': {
                'fire_or_mud': ( 'Fire or Mud', 'Firefox or Mudfish but not Airdog', 
                    ( rules['fire_or_mud'], rules['no_fr_or_de'], ) ),
            }
        })

        self.assert_snippets({
            '/1/Firefox/4.0/xxx/xxx/en-US/xxx/xxx/default/default/': (
                ( snippets['fire_or_mud'], True ), 
            ),
            '/1/Mudfish/4.0/xxx/xxx/en-GB/xxx/xxx/default/default/': (
                ( snippets['fire_or_mud'], True  ), 
            ),
            '/1/Firefox/4.0/xxx/xxx/de/xxx/xxx/default/default/': (
                ( snippets['fire_or_mud'], False  ), 
            ),
            '/1/Mudfish/4.0/xxx/xxx/fr/xxx/xxx/default/default/': (
                ( snippets['fire_or_mud'], False  ), 
            ),
            '/1/Airdog/4.0/xxx/xxx/en-GB/xxx/xxx/default/default/': (
                ( snippets['fire_or_mud'], False ), 
            ),
        })

    def test_unmatched_inclusion_rules(self):
        """Exercise inclusion rules that don't match"""

        rules = self.setup_rules({
            'fields': ('name', 'version', 'exclude'),
            'items': {
                'firefox': ('Firefox', None, False),
                '4.0': (None, '4.0', False),
            }
        })

        snippets = self.setup_snippets(rules, {
            'fields': ('name', 'body', 'rules'),
            'items': {
                'fire_4.0': ('Firefox 4.0', 'Firefox and 4.0',
                             (rules['firefox'], rules['4.0'])),
                'fire': ('Firefox', 'Firefox but not 4.0', (rules['firefox'],)),
                '4.0': ('4.0', '4.0 but not Firefox', (rules['4.0'],)),
            }
        })

        self.assert_snippets({
            '/1/Firefox/4.0/xxx/xxx/en-US/xxx/xxx/default/default/': (
                (snippets['fire_4.0'], True),
                (snippets['fire'], True),
                (snippets['4.0'], True),
            ),
            '/1/Firefox/3.0/xxx/xxx/en-US/xxx/xxx/default/default/': (
                (snippets['fire_4.0'], False),
                (snippets['fire'], True),
                (snippets['4.0'], False),
            ),
            '/1/Mudfish/4.0/xxx/xxx/en-US/xxx/xxx/default/default/': (
                (snippets['fire_4.0'], False),
                (snippets['fire'], False),
                (snippets['4.0'], True),
            ),
        })
