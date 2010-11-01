"""homesnippets common test utils"""
import logging
import time
import random
import datetime

from django.conf import settings

from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client

from django.core.cache import cache
from django.core.cache.backends import locmem

import homesnippets
from homesnippets.models import Snippet, ClientMatchRule

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr

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

