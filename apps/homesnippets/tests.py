"""
homesnippets app tests
"""
import logging

from django.conf import settings

from django.db import connection

from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client
 
from django.core.cache import cache


from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr

from homesnippets.models import Snippet, ClientMatchRule

class TestSnippetsMatch(TestCase):
    """Exercise selection of snippets via client match rules"""

    def setUp(self):
        self.log = logging.getLogger('nose.homesnippets')
        self.browser = Client()
        settings.DEBUG = True

        ClientMatchRule.objects.all().delete()
        Snippet.objects.all().delete()
        cache.clear()

    def tearDown(self):
        from django.db import connection
        #logging.debug(connection.queries)

    def test_simple_rules(self):
        """Exercise simple exact match rules"""

        rules = self.setup_rules({
            'fields': ( 'startpage_version', 'name', 'version', 'locale', ),
            'items': (
                # Specific rule, expected to be matched
                ( '1', 'Firefox', '4.0', 'en-US', ),
                # Less-specific rule, should match but not result in duplicate
                ( '1', 'Firefox', '4.0', None, ),
                # Rule that won't be attached to any snippet.
                ( '1', 'Mudfish', '7.0', 'en-GB', ),
                # Rule that will be attached to snippet, but not matched.
                ( '2', 'Airdog',  '3.0', 'de' ),
                # Rule matching anything
                ( None, None, None, None ),
            )
        })

        snippets = self.setup_snippets(rules, {
            'fields': ( 'name', 'body', 'rules' ),
            'items': (
                # Using specific and less-specific rule
                ( 'test 1', 'Expected body data', ( rules[0], rules[1] ) ),
                # No rules, so always included in results
                ( 'test 2', 'Ever-present body data', ( rules[4], ) ),
                # Rule attached that will never be matched, so should never appear
                (' test 3', 'Never-present body data', ( rules[3], ) ),
            )
        })

        self.assert_snippets({
            '/1/Firefox/4.0/xxx/xxx/en-US/xxx/xxx/default/default/': (
                ( snippets[0], True  ), ( snippets[1], True  ), ( snippets[2], False ),
            ),
            '/9/Waterduck/9.2/xxx/xxx/en-US/xxx/xxx/default/default/': (
                ( snippets[0], False ), ( snippets[1], True  ), ( snippets[2], False ),
            ),
            '/1/Mudfish/7.0/xxx/xxx/en-GB/xxx/xxx/default/default/': (
                ( snippets[0], False ), ( snippets[1], True  ), ( snippets[2], False ),
            ),
        })

    def test_exclusion_rules(self):
        """Exercise match rules that exclude snippets"""

        rules = self.setup_rules({
            'fields': ( 'startpage_version', 'name', 'version', 'locale', 'exclude' ),
            'items': (
                ( '1', 'Firefox', '4.0', 'en-US', True, ),
                ( '1', 'Firefox', '4.0', None, False, ),
                ( '1', 'Mudfish', '7.0', 'en-GB', True, ),
                ( '2', 'Airdog',  '3.0', 'de', False, ),
                ( '1', 'Windcat', '9.3', 'fr', True ),
                ( None, None, None, None, False ),
            )
        })

        snippets = self.setup_snippets(rules, {
            'fields': ( 'name', 'body', 'rules' ),
            'items': (
                ( 'test 1', 'Expected in en-GB but not en-US', ( rules[0], rules[1] ) ),
                ( 'test 2', 'Ever-present body data', ( rules[5], ) ),
                (' test 3', 'Never-present body data', ( rules[3], ) ),
                ( 'test 4', 'Usually-present body data', ( rules[5], rules[4], ) ),
            )
        })

        self.assert_snippets({
            '/1/Firefox/4.0/xxx/xxx/en-US/xxx/xxx/default/default/': (
                ( snippets[0], False ), ( snippets[1], True  ), 
                ( snippets[2], False ), ( snippets[3], True  ),
            ),
            '/1/Firefox/4.0/xxx/xxx/en-GB/xxx/xxx/default/default/': (
                ( snippets[0], True  ), ( snippets[1], True  ), 
                ( snippets[2], False ), ( snippets[3], True  ),
            ),
            '/1/Windcat/9.3/xxx/xxx/fr/xxx/xxx/default/default/': (
                ( snippets[0], False ), ( snippets[1], True  ), 
                ( snippets[2], False ), ( snippets[3], False ),
            ),
        })

    @attr("current")
    @attr("TODO")
    def test_regex_rules(self):
        """Exercise match rules that use regexes"""
        ok_(False)

    def setup_rules(self, rules_data):
        """Given a data structure defining client match rules, create the 
        model items"""
        rules = []
        for item in rules_data['items']:
            rule = ClientMatchRule(**dict(zip(rules_data['fields'], item)))
            rule.save()
            rules.append(rule)
        return rules

    def setup_snippets(self, rules, snippets_data):
        """Given a data structure defining snippets, create the model items"""
        snippets = []
        for item_data in snippets_data['items']:
            item = dict(zip(snippets_data['fields'], item_data))
            snippet = Snippet(name=item['name'], body=item['body'])
            snippet.save()
            snippets.append(snippet)
            for rule in item['rules']:
                snippet.client_match_rules.add(rule)
        return snippets

    def assert_snippets(self, tests):
        """Perform fetches against the snippet service, run content matches
        against the resulting content"""
        for path, expecteds in tests.items():
            resp = self.browser.get(path)
            #logging.debug('RESP %s' % resp.content)
            for e_snippet, e_present in expecteds:
                e_content = e_snippet.body
                #logging.debug("%s %s" % (e_present, e_content))
                eq_(resp.content.count(e_content), e_present and 1 or 0,
                    'Snippet "%s" should%sappear in content for %s' % (
                        e_content, e_present and ' ' or ' not ', path))

