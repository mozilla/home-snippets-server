"""
homesnippets caching tests
"""
import time
import random

from django.conf import settings
from django.core import cache
from django.core.cache.backends import locmem

from nose.tools import eq_, ok_

import homesnippets.models
from homesnippets.models import (Snippet, ClientMatchRule,
                                 CACHE_RULE_MATCH_PREFIX,
                                 CACHE_RULE_LASTMOD_PREFIX,
                                 CACHE_RULE_ALL_PREFIX,
                                 CACHE_RULE_ALL_LASTMOD_PREFIX,
                                 CACHE_RULE_NEW_LASTMOD_PREFIX,
                                 CACHE_SNIPPET_LASTMOD_PREFIX,
                                 CACHE_SNIPPET_LOOKUP_PREFIX)
from homesnippets.tests.utils import HomesnippetsTestCase


class CacheClass(locmem.CacheClass):
    """Cache subclass that comes with a hacky event log for test assertions"""

    def __init__(self, server, params):
        locmem.CacheClass.__init__(self, server, params)
        self.id = random.randint(0, 1000)
        self.log = []
        self.during_many = False

    def get(self, key, default=None):
        if not self.during_many:
            self.log.append(('get', key))
        return locmem.CacheClass.get(self, key, default)

    def set(self, key, value, timeout=None):
        if not self.during_many:
            self.log.append(('set', key, value))
        return locmem.CacheClass.set(self, key, value, timeout)

    def clear(self):
        self.log = []
        return locmem.CacheClass.clear(self)

    def get_many(self, keys):
        self.log.append(('get_many', keys))
        self.during_many = True
        rv = locmem.CacheClass.get_many(self, keys)
        self.during_many = False
        return rv

    def set_many(self, keys, timeout):
        self.log.append(('set_many', keys, timeout))
        self.during_many = True
        rv = locmem.CacheClass.set_many(self, keys, timeout)
        self.during_many = False
        return rv


class TestSnippetsCache(HomesnippetsTestCase):

    def setUp(self):
        HomesnippetsTestCase.setUp(self)

        settings.CACHE_BACKEND = 'homesnippets.tests://'
        self.cache = cache.get_cache(settings.CACHE_BACKEND)
        cache.cache = self.cache
        homesnippets.models.cache = self.cache
        self.cache.clear()

        self.rules = self.setup_rules({
            'fields': ('startpage_version', 'name', 'version', 'locale'),
            'items': {
                # Specific rule, expected to be matched
                'specific': ('1', 'Firefox', '4.0', 'en-US'),
                # Less-specific rule, should match but not result in duplicate
                'vague': ('1', 'Firefox', '4.0', None),
                # Rule that won't be attached to any snippet.
                'unused': ('1', 'Mudfish', '7.0', 'en-GB'),
                # Rule that will be attached to snippet, but not matched.
                'unmatched': ('2', 'Airdog',  '3.0', 'de'),
                # Rule matching anything
                'all': (None, None, None, None),
            }
        })

        self.snippets = self.setup_snippets(self.rules, {
            'fields': ('name', 'body', 'rules'),
            'items': {
                # Using specific and less-specific rule
                'expected': ('test 1', 'Expected body data',
                             (self.rules['specific'], self.rules['vague'])),
                # No rules, so always included in results
                'ever': ('test 2', 'Ever-present body data',
                         (self.rules['all'], )),
                # Rule attached that will never be matched,
                # so should never appear
                'never': ('test 3', 'Never-present body data',
                          (self.rules['unmatched'], )),
            }
        })

        # Warm up the cache with some initial requests...
        self.assert_snippets({
            '/1/Firefox/4.0/xxx/xxx/en-US/xxx/xxx/default/default/': (
                (self.snippets['expected'], True),
                (self.snippets['ever'], True),
                (self.snippets['never'], False),
            ),
            '/9/Waterduck/9.2/xxx/xxx/en-US/xxx/xxx/default/default/': (
                (self.snippets['expected'], False),
                (self.snippets['ever'], True),
                (self.snippets['never'], False),
            ),
            '/1/Mudfish/7.0/xxx/xxx/en-GB/xxx/xxx/default/default/': (
                (self.snippets['expected'], False),
                (self.snippets['ever'], True),
                (self.snippets['never'], False),
            ),
        })

        # Looking for this pattern of cache access should be good enough for
        # ensuring things are working so far...
        self.assert_cache_events((

            # First, the lastmod times for rules are cached
            ('set_many', [CACHE_RULE_LASTMOD_PREFIX,
                CACHE_RULE_ALL_LASTMOD_PREFIX, CACHE_RULE_NEW_LASTMOD_PREFIX]),
            ('set_many', [CACHE_RULE_LASTMOD_PREFIX,
                CACHE_RULE_ALL_LASTMOD_PREFIX, CACHE_RULE_NEW_LASTMOD_PREFIX]),
            ('set_many', [CACHE_RULE_LASTMOD_PREFIX,
                CACHE_RULE_ALL_LASTMOD_PREFIX, CACHE_RULE_NEW_LASTMOD_PREFIX]),
            ('set_many', [CACHE_RULE_LASTMOD_PREFIX,
                CACHE_RULE_ALL_LASTMOD_PREFIX, CACHE_RULE_NEW_LASTMOD_PREFIX]),
            ('set_many', [CACHE_RULE_LASTMOD_PREFIX,
                CACHE_RULE_ALL_LASTMOD_PREFIX, CACHE_RULE_NEW_LASTMOD_PREFIX]),

            # Then, lastmod times for snippets are cached.
            ('set_many', [CACHE_SNIPPET_LASTMOD_PREFIX]),
            ('set_many', [CACHE_SNIPPET_LASTMOD_PREFIX]),
            ('set_many', [CACHE_SNIPPET_LASTMOD_PREFIX]),

            # Request 1
            ('get', CACHE_RULE_MATCH_PREFIX),
            ('get_many', [CACHE_RULE_ALL_PREFIX,
                          CACHE_RULE_ALL_LASTMOD_PREFIX]),
            ('set', CACHE_RULE_ALL_PREFIX),
            ('set', CACHE_RULE_MATCH_PREFIX),
            ('get', CACHE_SNIPPET_LOOKUP_PREFIX),
            ('set', CACHE_SNIPPET_LOOKUP_PREFIX),

            # Request 2
            ('get', CACHE_RULE_MATCH_PREFIX),
            ('get_many', [CACHE_RULE_ALL_PREFIX,
                          CACHE_RULE_ALL_LASTMOD_PREFIX]),
            ('set', CACHE_RULE_MATCH_PREFIX),
            ('get', CACHE_SNIPPET_LOOKUP_PREFIX),
            ('set', CACHE_SNIPPET_LOOKUP_PREFIX),

            # Request 3
            ('get', CACHE_RULE_MATCH_PREFIX),
            ('get_many', [CACHE_RULE_ALL_PREFIX,
                          CACHE_RULE_ALL_LASTMOD_PREFIX]),
            ('set', CACHE_RULE_MATCH_PREFIX),
            ('get', CACHE_SNIPPET_LOOKUP_PREFIX),
            ('set', CACHE_SNIPPET_LOOKUP_PREFIX),

        ))

        # Ensure clock ticks before further cache activity
        time.sleep(1)

    def test_cache_hits(self):
        """Exercise cache hits with no cause for invalidation"""

        self.assert_snippets({
            '/1/Firefox/4.0/xxx/xxx/en-US/xxx/xxx/default/default/': (
                (self.snippets['expected'], True),
                (self.snippets['ever'], True),
                (self.snippets['never'], False),
            ),
            '/9/Waterduck/9.2/xxx/xxx/en-US/xxx/xxx/default/default/': (
                (self.snippets['expected'], False),
                (self.snippets['ever'], True),
                (self.snippets['never'], False),
            ),
            '/1/Mudfish/7.0/xxx/xxx/en-GB/xxx/xxx/default/default/': (
                (self.snippets['expected'], False),
                (self.snippets['ever'], True),
                (self.snippets['never'], False),
            ),
        })

        # These requests should be nothing but cache hits, eg. no set's
        self.assert_cache_events((

            # Request 1
            ('get', CACHE_RULE_MATCH_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_NEW_LASTMOD_PREFIX]),
            ('get', CACHE_SNIPPET_LOOKUP_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX]),

            # Request 2
            ('get', CACHE_RULE_MATCH_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX]),
            ('get', CACHE_SNIPPET_LOOKUP_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_SNIPPET_LASTMOD_PREFIX]),

            # Request 3
            ('get', CACHE_RULE_MATCH_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_NEW_LASTMOD_PREFIX]),
            ('get', CACHE_SNIPPET_LOOKUP_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_SNIPPET_LASTMOD_PREFIX]),

        ))

    def test_invalidation_on_rule_change(self):
        """Exercise cache invalidation on change to a client match rule"""

        # Change a rule, which should invalidate cached results for snippets
        self.rules['vague'].description = 'changed'
        self.rules['vague'].save()

        self.assert_snippets({
            '/1/Firefox/4.0/xxx/xxx/en-US/xxx/xxx/default/default/': (
                (self.snippets['expected'], True),
                (self.snippets['ever'], True),
                (self.snippets['never'], False),
            ),
        })

        self.assert_cache_events((

            # Rule content changed.
            ('set_many', [CACHE_RULE_LASTMOD_PREFIX,
                CACHE_RULE_ALL_LASTMOD_PREFIX]),

            # Rule cache miss
            ('get', CACHE_RULE_MATCH_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_NEW_LASTMOD_PREFIX]),

            # All rules cache miss
            ('get_many', [CACHE_RULE_ALL_PREFIX,
                          CACHE_RULE_ALL_LASTMOD_PREFIX]),
            ('set', CACHE_RULE_ALL_PREFIX),

            ('set', CACHE_RULE_MATCH_PREFIX),

            # Snippet cache miss
            ('get', CACHE_SNIPPET_LOOKUP_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_SNIPPET_LASTMOD_PREFIX,
                          CACHE_SNIPPET_LASTMOD_PREFIX]),

            ('set', CACHE_SNIPPET_LOOKUP_PREFIX),

        ))

    def test_invalidation_on_snippet_change(self):
        """Exercise cache invalidation on change to a snippet"""

        # Change a snippet, which should invalidate cached results for snippets
        self.snippets['ever'].name = 'changed'
        self.snippets['ever'].save()

        self.assert_snippets({
            '/9/Waterduck/9.2/xxx/xxx/en-US/xxx/xxx/default/default/': (
                (self.snippets['expected'], False),
                (self.snippets['ever'], True),
                (self.snippets['never'], False),
            ),
        })

        self.assert_cache_events((

            # Snippet content changed, bumps rules as well.
            ('set_many', [CACHE_SNIPPET_LASTMOD_PREFIX,
                CACHE_RULE_LASTMOD_PREFIX]),

            # Rule cache miss
            ('get', CACHE_RULE_MATCH_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_NEW_LASTMOD_PREFIX]),
            ('get_many', [CACHE_RULE_ALL_PREFIX,
                          CACHE_RULE_ALL_LASTMOD_PREFIX]),
            ('set', CACHE_RULE_MATCH_PREFIX),

            # Snippet cache miss
            ('get', CACHE_SNIPPET_LOOKUP_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_SNIPPET_LASTMOD_PREFIX]),
            ('set', CACHE_SNIPPET_LOOKUP_PREFIX),

        ))

    def test_invalidation_with_url_variety(self):
        """
        Exercise cache with a variety of URLs resulting in the same snippets
        """

        # Change a snippet, which should invalidate cached results for snippets
        self.snippets['ever'].body = 'changed_again'
        self.snippets['ever'].save()

        # Try multiple URLs that result in the same set of matching rules,
        # should cause cache misses in rules, but not in snippet lookup
        for idx in (0, 1):
            self.assert_snippets({
                '/1/Alpha/4.0/xxx/xxx/en-US/xxx/xxx/default/default/': (
                    (self.snippets['ever'], True),
                ),
                '/1/Beta/9.2/xxx/xxx/en-US/xxx/xxx/default/default/': (
                    (self.snippets['ever'], True),
                ),
                '/1/Gamma/7.0/xxx/xxx/en-GB/xxx/xxx/default/default/': (
                    (self.snippets['ever'], True),
                ),
            })

        self.assert_cache_events((

            # Content changed
            ('set_many', [CACHE_SNIPPET_LASTMOD_PREFIX,
                CACHE_RULE_LASTMOD_PREFIX]),

            # Request #1 - cache miss on rules and snippets
            ('get', CACHE_RULE_MATCH_PREFIX),
            ('get_many', [CACHE_RULE_ALL_PREFIX,
                          CACHE_RULE_ALL_LASTMOD_PREFIX]),
            ('set', CACHE_RULE_MATCH_PREFIX),
            ('get', CACHE_SNIPPET_LOOKUP_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_SNIPPET_LASTMOD_PREFIX]),
            # Snippets looked up & cached for this request only
            ('set', CACHE_SNIPPET_LOOKUP_PREFIX),

            # Request #2 - cache miss on rules, but hit on snippets
            ('get', CACHE_RULE_MATCH_PREFIX),
            ('get_many', [CACHE_RULE_ALL_PREFIX,
                          CACHE_RULE_ALL_LASTMOD_PREFIX]),
            ('set', CACHE_RULE_MATCH_PREFIX),
            ('get', CACHE_SNIPPET_LOOKUP_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_SNIPPET_LASTMOD_PREFIX]),

            # Request #3 - cache miss on rules, but hit on snippets
            ('get', CACHE_RULE_MATCH_PREFIX),
            ('get_many', [CACHE_RULE_ALL_PREFIX,
                          CACHE_RULE_ALL_LASTMOD_PREFIX]),
            ('set', CACHE_RULE_MATCH_PREFIX),
            ('get', CACHE_SNIPPET_LOOKUP_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_SNIPPET_LASTMOD_PREFIX]),

            # Request #4 - cache hits, all around
            ('get', CACHE_RULE_MATCH_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_NEW_LASTMOD_PREFIX]),
            ('get', CACHE_SNIPPET_LOOKUP_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_SNIPPET_LASTMOD_PREFIX]),

            # Request #5 - cache hits, all around
            ('get', CACHE_RULE_MATCH_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_NEW_LASTMOD_PREFIX]),
            ('get', CACHE_SNIPPET_LOOKUP_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_SNIPPET_LASTMOD_PREFIX]),

            # Request #6 - cache hits, all around
            ('get', CACHE_RULE_MATCH_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_NEW_LASTMOD_PREFIX]),
            ('get', CACHE_SNIPPET_LOOKUP_PREFIX),
            ('get_many', [CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX, CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_RULE_LASTMOD_PREFIX,
                          CACHE_SNIPPET_LASTMOD_PREFIX]),

        ))

    def test_new_rule_creation(self):
        """Exercise cache invalidation on new rule creation"""

        new_rule = ClientMatchRule(locale='en-GB')
        new_rule.save()

        new_snippet = Snippet(body='GB English only!')
        new_snippet.save()
        new_snippet.client_match_rules.add(new_rule)

        self.assert_snippets({
            '/1/Gamma/7.0/xxx/xxx/en-GB/xxx/xxx/default/default/': (
                (new_snippet, True),
            ),
        })

    def assert_cache_events(self, expected_events):
        """Match up a set of expected cache events and prefixes with the cache
        log. Clears the log after a successful assertion set."""

        expected_events = list(expected_events)
        while expected_events:
            expected = expected_events.pop(0)
            result = self.cache.log.pop(0)

            eq_(expected[0], result[0])

            if type(expected[1]) is str:
                ok_(result[1].startswith(expected[1]),
                    '%s should start with %s' % (result[1], expected[1]))

            else:
                prefixes = expected[1]
                prefixes.sort()
                if 'get_many' == expected[0]:
                    result_keys = result[1]
                elif 'set_many' == expected[0]:
                    result_keys = result[1].keys()
                    result_keys.sort()

                for idx2 in range(0, len(prefixes)):
                    ok_(result_keys[idx2].startswith(prefixes[idx2]),
                        '%s should start with %s' % (
                            result_keys[idx2], prefixes[idx2]))

        result_len = len(self.cache.log)
        eq_(0, result_len,
            'Cache events should be exhausted, but %s left' % (result_len,))

        self.cache.log = []
