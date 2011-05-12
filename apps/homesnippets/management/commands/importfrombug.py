"""
Imports snippet translations from bug attachments - see bug 636815

This management command was built specifically to scrape content from
attachments to bug 636815 and create the appropriate client match rules and
snippets.

Someday, I hope something like this could be useful for future snippet updates
with Bugzilla-based localization. This might mean writing a JSON build file
with overrides for constants below.

Ideally, this tool should result in new rules and snippets only on the first
run where they're missing. Subsequent runs should update existing snippets and
rules with new content, leaving primary keys alone. That should ease the bulk
export and load of model objects as JSON from the Django admin pages.
"""
import os, sys, re, cgi, urllib, json, base64
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from homesnippets.models import ClientMatchRule, Snippet


# URL for JSON representation of known shipping languages
LANG_JSON_URL = getattr(settings, 'LANG_JSON_URL', 
    'http://svn.mozilla.org/libs/product-details/json/languages.json')

# URL template for grabbing a bug's attachments in JSON form.
BUG_JSON_URL = getattr(settings, 'BUG_JSON_URL',
    'https://api-dev.bugzilla.mozilla.org/latest/bug/%(bug_id)s/attachment?attachmentdata=1')


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
    )

    def handle(self, *args, **options):

        if len(args) < 1:
            print "Usage: manage.py importfrombug import-manifest.json"
            sys.exit(1)

        self.import_manifest = json.load(open(args[0], 'r'))

        # TODO: Read all of this in from a JSON build file.
        self.bug_id = self.import_manifest['bug_id']

        self.update_locale_rules()
        self.update_snippets()

    def update_locale_rules(self):
        """Ensure a ClientMatchRule exists for each known locale"""

        print "Fetching Firefox product languages"
        self.lang_data = json.load(urllib.urlopen(LANG_JSON_URL))

        # Built a case-insensitive map of known locale codes.
        self.locales = dict()
        for code, details in self.lang_data.items():
            self.locales[code.lower()] = dict( code=code, name=details['English'] )

        print "Updating locale match rules"
        ( rules_created, rules_updated ) = ( [], [] )
        for code, details in self.lang_data.items():

            defaults = dict()
            for k, v in self.import_manifest['rule_defaults'].items():
                defaults[k] = v % dict(
                    locale=code, 
                    name=details['English']
                )

            ( rule, created ) = ClientMatchRule.objects.get_or_create(
                description=defaults['description'])
            
            for k, v in defaults.items():
                setattr(rule, k, v)

            rule.save()

            if created:
                rules_created.append(code)
            else:
                rules_updated.append(code)

        print "Created: %s" % rules_created
        print "Updated: %s" % rules_updated
        
    def update_snippets(self):
        """Update snippets from bug attachments"""

        print "Fetching data for bug %s" % self.bug_id
        self.bug_data = json.load(urllib.urlopen(BUG_JSON_URL % {'bug_id':self.bug_id}))

        icon_img_cache = dict()

        # Iterate through all attachments found in the bug. Parse out locale
        # code from description, decode data and parse out english/translation
        # pairs, create/update snippets from the content.
        PAREN_RE = re.compile(r"\(([^)]+)\)")
        bad_attachments = []
        for attachment in self.bug_data['attachments']:
            locale, data = None, None
            
            if attachment['is_obsolete'] == 1:
                continue
            
            # Look for the last thing in parentheses in the attachment
            # description, use that as the locale code.
            matches = PAREN_RE.findall(attachment['description'])
            if matches and matches[-1].lower() in self.locales:
                locale = self.locales[matches[-1].lower()]

            if not locale:
                bad_attachments.append(attachment)
                print 'BAD LOCALE: %s' % (matches[-1])
                continue

            print "%s" % ( locale, )

            # Look up the match rule created earlier for this locale.
            rule = ClientMatchRule.objects.get(
                description=self.import_manifest['rule_defaults']['description'] % dict(
                    name=locale['name'], locale=locale['code']))

            # Attachment data should show up in the JSON as base64. Haven't
            # seen another kind of encoding so far, but we could be surprised.
            if 'base64' == attachment['encoding']:
                data = unicode(base64.b64decode(attachment['data']), 'utf-8')
                open('trans-%s.txt' % locale['code'], 'w').write(data.encode('utf-8'))
            else:
                bad_attachments.append(attachment)
                print 'BAD DATA: %s' % (matches[-1])

            # L10N format for each snippet in an attachment is:
            #
            #     ;english string
            #     locale translation
            #     {blank line}
            # 
            # So, parse that into english/translated pairs.
            snippets, english, translated = [], None, None
            lines = data.splitlines() + [u'']
            BOM_SEMI = unicode("\xef\xbb\xbf;", 'utf-8')
            for line in lines:
                line = line.strip()
                # HACK: Some attachments started with UTF-8 BOM marker, so look for that too
                if line.startswith(";") or line.startswith(BOM_SEMI):
                    english = line[line.index(';')+1:]
                elif line:
                    translated = line
                else:
                    if english and translated:
                        snippets.append(( english, translated ))
                    english, translated = None, None

            # Now that the english/translation pairs are parsed out, iterate
            # through what we have, pair each up with snippet metadata,
            # create/update a snippet from templates filled with translation
            # and metadata
            s_updated, s_created, idx = [], [], 0
            for english, translated in snippets:
                idx += 1

                if english not in self.import_manifest['snippets_content']:
                    print "\t%s UNEXPECTED ENGLISH: %s" % (idx, english)
                    continue

                meta = self.import_manifest['snippets_content'][english]

                if 'disabled' in meta and meta['disabled']: continue

                meta.update(dict(
                    bug_id = self.bug_id,
                    attachment_description = attachment['description'],
                    locale_code = locale['code'],
                    locale_name = locale['name'],
                    english = english,
                    translated = translated % cgi.escape(meta['placeholder']),
                ))

                # Quick and dirty image-to-data: URL conversion if there's an
                # icon_url_src pointing at an image.
                if 'icon_url_src' in meta and meta['icon_url_src']:
                    if meta['icon_url_src'] not in icon_img_cache:
                        data = urllib.urlopen(meta['icon_url_src'])
                        enc = urllib.quote(base64.b64encode(data.read()))
                        type = data.info()['content-type'].split(';')[0]
                        icon_img_cache[meta['icon_url_src']] = ('data:%s;base64,%s' % ( type, enc ))
                    meta['icon_url'] = icon_img_cache[meta['icon_url_src']] 
                else :
                    meta['icon_url'] = ''

                snippet_props = dict()
                for k,v in self.import_manifest['snippet_defaults'].items():
                    snippet_props[k] = v % meta
                snippet_props.update(meta)

                ( snippet, created ) = Snippet.objects.get_or_create(name=snippet_props['name'])
                for k,v in snippet_props.items():
                    setattr(snippet, k, v);
                snippet.client_match_rules = [ rule ]
                snippet.save()

                # TODO: Need a -verbose level option to turn this on and off
                # print "\t%s (%s) %s" % ( idx, ['updated','created'][created], english )

                if created: s_created.append(snippet)
                else: s_updated.append(snippet)

            # TODO: Need a -verbose level option to turn this on and off
            print "Created %s / Updated %s" % ( len(s_created), len(s_updated) )

        # Report on bad attachments whose locale or data was unreadable.
        # TODO: Need a -verbose level option to turn this on and off
        print "BAD: %s" % ( len(bad_attachments) )
        for attachment in bad_attachments:
            print attachment
