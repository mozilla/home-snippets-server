from pyquery import PyQuery as pq

from homesnippets.tests.utils import HomesnippetsTestCase


class ViewSnippetsTests(HomesnippetsTestCase):
    def test_snippet_country(self):
        """
        If a snippet has a country, it should have the data-country attribute
        set on it's container. Otherwise, it should not have the attribute.
        """
        rules = self.setup_rules({
            'fields': (),
            'items': {
                'all': (),
            }
        })

        snippets = self.setup_snippets(rules, {
            'fields': ('name', 'body', 'country', 'rules'),
            'items': {
                'test1': ('Test1', 'test1', 'us', (rules['all'],)),
                'test2': ('Test2', 'test2', '', (rules['all'],)),
            }
        })

        response = self.browser.get('/1/Firefox/4.0/xxx/xxx/en-US/xxx/xxx/'
                                    'default/default/')
        d = pq(response.content)
        test1 = d('div[data-snippet-id="%s"]' % snippets['test1'].id)
        test2 = d('div[data-snippet-id="%s"]' % snippets['test2'].id)

        self.assertEqual(test1.attr('data-country'), 'us')
        self.assertEqual(test2.attr('data-country'), None)  # Doesn't exist.
