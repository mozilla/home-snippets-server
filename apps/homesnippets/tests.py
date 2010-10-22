"""
homesnippets app tests
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
from homesnippets.models import CACHE_RULE_MATCH_PREFIX, CACHE_RULE_LASTMOD_PREFIX
from homesnippets.models import CACHE_SNIPPET_MATCH_PREFIX
from homesnippets.models import CACHE_SNIPPET_LASTMOD_PREFIX

import django.core.cache
import homesnippets.models

class HomesnippetsTestCase(TestCase):

    def setUp(self):
        self.log = logging.getLogger('nose.homesnippets')
        self.browser = Client()

        settings.DEBUG = True

        ClientMatchRule.objects.all().delete()
        Snippet.objects.all().delete()
        
        homesnippets.models.cache.clear()

    def tearDown(self):
        from django.db import connection
        #logging.debug(connection.queries)

    def setup_rules(self, rules_data):
        """Given a data structure defining client match rules, create the 
        model items"""
        rules = {}
        for name, item in rules_data['items'].items():
            rules[name] = ClientMatchRule(**dict(zip(rules_data['fields'], item)))
            rules[name].save()
        return rules

    def setup_snippets(self, rules, snippets_data):
        """Given a data structure defining snippets, create the model items"""
        snippets = {}
        for name, item_data in snippets_data['items'].items():
            
            item = dict(zip(snippets_data['fields'], item_data))
            if not 'name' in item:
                item['name'] = name

            rules = item['rules']
            del item['rules']

            snippets[name] = Snippet(**item)
            snippets[name].save()

            for rule in rules:
                snippets[name].client_match_rules.add(rule)

        return snippets

    def assert_snippets(self, tests):
        """Perform fetches against the snippet service, run content matches
        against the resulting content"""
        for path, expecteds in tests.items():
            resp = self.browser.get(path)
            for e_snippet, e_present in expecteds:
                e_content = e_snippet.body
                eq_(resp.content.count(e_content), e_present and 1 or 0,
                    'Snippet "%s" should%sappear in content for %s' % (
                        e_content, e_present and ' ' or ' not ', path))


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


class CacheClass(locmem.CacheClass):
    """Cache subclass that comes with a hacky event log for test assertions"""

    def __init__(self, server, params):
        locmem.CacheClass.__init__(self, server, params)
        self.id = random.randint(0,1000)
        self.log = []

    def get(self, key, default=None):
        self.log.append(('get', key))
        return locmem.CacheClass.get(self,key,default)

    def get_many(self, keys):
        self.log.append(('get_many', keys))
        return locmem.CacheClass.get_many(self,keys)

    def set(self, key, value, timeout=None):
        self.log.append(('set', key, value))
        return locmem.CacheClass.set(self,key,value,timeout)

    def clear(self):
        self.log = []
        return locmem.CacheClass.clear(self)


class TestSnippetsCache(HomesnippetsTestCase):

    def setUp(self):
        HomesnippetsTestCase.setUp(self)

        settings.CACHE_BACKEND = 'homesnippets.tests://'
        self.cache = django.core.cache.get_cache(settings.CACHE_BACKEND)
        django.core.cache.cache = self.cache
        homesnippets.models.cache = self.cache
        self.cache.clear()

    def test_cache_invalidation(self):
        """Exercise cache invalidation through modification of rules and snippets"""

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

        # Kind of a hack, but looking for this general pattern of cache access
        # should be good enough for ensuring things are working so far...
        self.assert_cache_events((

            # First, the lastmod times for rules are cached
            ('set', CACHE_RULE_LASTMOD_PREFIX),
            ('set', CACHE_RULE_LASTMOD_PREFIX),
            ('set', CACHE_RULE_LASTMOD_PREFIX),
            ('set', CACHE_RULE_LASTMOD_PREFIX),
            ('set', CACHE_RULE_LASTMOD_PREFIX),

            # Then, lastmod times for snippets are cached.
            ('set', CACHE_SNIPPET_LASTMOD_PREFIX),
            ('set', CACHE_SNIPPET_LASTMOD_PREFIX),
            ('set', CACHE_SNIPPET_LASTMOD_PREFIX),

            # Request 1
            ('get', CACHE_SNIPPET_MATCH_PREFIX),
            ('get', CACHE_RULE_MATCH_PREFIX),
            ('set', CACHE_RULE_MATCH_PREFIX),
            ('set', CACHE_SNIPPET_MATCH_PREFIX),

            # Request 2
            ('get', CACHE_SNIPPET_MATCH_PREFIX),
            ('get', CACHE_RULE_MATCH_PREFIX),
            ('set', CACHE_RULE_MATCH_PREFIX),
            ('set', CACHE_SNIPPET_MATCH_PREFIX),

            # Request 3
            ('get', CACHE_SNIPPET_MATCH_PREFIX),
            ('get', CACHE_RULE_MATCH_PREFIX),
            ('set', CACHE_RULE_MATCH_PREFIX),
            ('set', CACHE_SNIPPET_MATCH_PREFIX),
            
        ))

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

        # These requests should be nothing but cache hits, eg. no set's
        self.assert_cache_events((

            # Request 1
            ('get', CACHE_SNIPPET_MATCH_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX, 
                CACHE_RULE_LASTMOD_PREFIX, CACHE_SNIPPET_LASTMOD_PREFIX, 
                CACHE_SNIPPET_LASTMOD_PREFIX]),
            ('get', CACHE_RULE_LASTMOD_PREFIX),
            ('get', CACHE_RULE_LASTMOD_PREFIX),
            ('get', CACHE_RULE_LASTMOD_PREFIX),
            ('get', CACHE_SNIPPET_LASTMOD_PREFIX),
            ('get', CACHE_SNIPPET_LASTMOD_PREFIX),

            # Request 2
            ('get', CACHE_SNIPPET_MATCH_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX, 
                CACHE_SNIPPET_LASTMOD_PREFIX]),
            ('get', CACHE_RULE_LASTMOD_PREFIX),
            ('get', CACHE_RULE_LASTMOD_PREFIX),
            ('get', CACHE_SNIPPET_LASTMOD_PREFIX),

            # Request 3
            ('get', CACHE_SNIPPET_MATCH_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_SNIPPET_LASTMOD_PREFIX]),
            ('get', CACHE_RULE_LASTMOD_PREFIX),
            ('get', CACHE_SNIPPET_LASTMOD_PREFIX),

        ))

        # Change a rule, which should invalidate cached results for snippets
        time.sleep(1) # ensure the clock ticks
        rules['vague'].description = 'changed'
        rules['vague'].save()

        self.assert_snippets({
            '/1/Firefox/4.0/xxx/xxx/en-US/xxx/xxx/default/default/': (
                ( snippets['expected'], True  ), 
                ( snippets['ever'], True  ), 
                ( snippets['never'], False ),
            ),
        })

        self.assert_cache_events((
            # The test changes a rule
            ('set', CACHE_RULE_LASTMOD_PREFIX),

            # Try fetching cached snippet match
            ('get', CACHE_SNIPPET_MATCH_PREFIX),
            
            # Check the lastmods for both snippets and rules...
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX, 
                CACHE_RULE_LASTMOD_PREFIX, CACHE_SNIPPET_LASTMOD_PREFIX, 
                CACHE_SNIPPET_LASTMOD_PREFIX]),
            ('get', CACHE_RULE_LASTMOD_PREFIX),
            ('get', CACHE_RULE_LASTMOD_PREFIX),
            ('get', CACHE_RULE_LASTMOD_PREFIX),
            ('get', CACHE_SNIPPET_LASTMOD_PREFIX),
            ('get', CACHE_SNIPPET_LASTMOD_PREFIX),
            
            # Whoops, one of the lastmods changed, so check the rules...
            ('get', CACHE_RULE_MATCH_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX, 
                CACHE_RULE_LASTMOD_PREFIX]),
            ('get', CACHE_RULE_LASTMOD_PREFIX),
            ('get', CACHE_RULE_LASTMOD_PREFIX),
            ('get', CACHE_RULE_LASTMOD_PREFIX),
            
            # Since a rule was changed, the matching set is recalculated and
            # cached again.
            ('set', CACHE_RULE_MATCH_PREFIX),
            
            # Since the rule matches changed, find the matching snippets again
            # and cache those.
            ('set', CACHE_SNIPPET_MATCH_PREFIX),
        ))

        # Change a snippet, which should invalidate cached results for snippets
        time.sleep(1) # ensure the clock ticks
        snippets['ever'].name = 'changed'
        snippets['ever'].save()

        self.assert_snippets({
            '/9/Waterduck/9.2/xxx/xxx/en-US/xxx/xxx/default/default/': (
                ( snippets['expected'], False ), 
                ( snippets['ever'], True  ), 
                ( snippets['never'], False ),
            ),
        })

        self.assert_cache_events((
            # Test changes a snippet, which also bumps the rule
            ('set', CACHE_SNIPPET_LASTMOD_PREFIX),
            ('set', CACHE_RULE_LASTMOD_PREFIX),
            
            # Try getting a snippet match
            ('get', CACHE_SNIPPET_MATCH_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_SNIPPET_LASTMOD_PREFIX]),
            ('get', CACHE_RULE_LASTMOD_PREFIX),
            ('get', CACHE_SNIPPET_LASTMOD_PREFIX),
            ('get', CACHE_RULE_MATCH_PREFIX),
            
            # Snippet match was a miss, so try hitting rules again.
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX]),
            ('get', CACHE_RULE_LASTMOD_PREFIX),
            
            # Both the rule match and snippet set are cached
            ('set', CACHE_RULE_MATCH_PREFIX),
            ('set', CACHE_SNIPPET_MATCH_PREFIX),
        ))

    def assert_cache_events(self, expected_events):
        """Match up a set of expected cache events and prefixes with the cache
        log. Clears the log after a successful assertion set."""

        expected_len = len(expected_events)
        result_len = len(self.cache.log)
        eq_(expected_len, result_len,
            'There should be %s cache events, not %s' % (expected_len, result_len))

        for idx in range(0, len(expected_events)):
            expected = expected_events[idx]
            result   = self.cache.log[idx]
            eq_(expected[0], result[0])
            if type(expected[1]) is str:
                ok_(result[1].startswith(expected[1]),
                    '%s should start with %s' % (result[1], expected[1] ))
            else:
                prefixes = expected[1]
                for idx2 in range(0, len(prefixes)):
                    ok_(result[1][idx2].startswith(prefixes[idx2]),
                        '%s should start with %s' % (
                            result[1][idx2], expected[1][idx2] ))

        self.cache.log = []
