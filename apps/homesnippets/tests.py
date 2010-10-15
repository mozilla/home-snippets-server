"""
homesnippets app tests
"""
import logging
import time

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

    #######################################################################

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
            snippets[name] = Snippet(name=item['name'], body=item['body'])
            snippets[name].save()
            for rule in item['rules']:
                snippets[name].client_match_rules.add(rule)
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

