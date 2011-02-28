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
import os, sys, re, urllib, json, base64
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from homesnippets.models import ClientMatchRule, Snippet


# TODO: Most/all of these constants should be specified via a JSON build
# config file and/or command-line options to make this command more flexible.

BUG_ID = '636815'

# URL for JSON representation of known shipping languages
LANG_JSON_URL = getattr(settings, 'LANG_JSON_URL', 
    'http://svn.mozilla.org/libs/product-details/json/languages.json')
# URL template for grabbing a bug's attachments in JSON form.
BUG_JSON_URL = getattr(settings, 'BUG_JSON_URL',
    'https://api-dev.bugzilla.mozilla.org/latest/bug/%(bug_id)s/attachment?attachmentdata=1')

# Description template used for naming per-locale client match rules
RULE_DESCRIPTION_TMPL = '%(code)s locale (%(name)s), Firefox v4.*'
# Name template used in naming each generated snippet
SNIPPET_NAME_TMPL = 'Bug %(bug_id)s: %(attachment_description)s - %(english)s'
# HTML template used to construct HTML content for each snippet.
SNIPPET_HTML_TMPL = """<div class="snippet">
    <img src="%(icon_url)s" />
    <p>%(translation)s</p>
</div>"""

# Metadata associated with each snippet by English text
# icon_url: a data: URI for an icon image
# snippet_url: URL used for the single %s placeholder 
TRANSLATIONS_META = {
    """Firefox 4 is here: new look, more speed, extra awesomeness. <a href="%s">Download today!</a>""": 
        dict( icon_url='', snippet_url='http://example.com' ),
    """Firefox 4 is here! <a href="%s">Download it today</a> and put the Web on fast forward.""": 
        dict( icon_url='', snippet_url='http://example.com' ),
    """Take Firefox 4 anywhere you go! Firefox 4 for Android and Maemo is live and ready for you to enjoy. <a href="%s">Get it now</a>.""": 
        dict( icon_url='', snippet_url='http://example.com' ),
    """Now that you've got Firefox 4, <a href="%s">learn about all the cool things</a> you can do with your new browser.""": 
        dict( icon_url='', snippet_url='http://example.com' ),
    """Want to see what the Web is really capable of? <a href="%s">Explore the Web o' Wonder demo gallery</a> and prepare to be amazed!""": 
        dict( icon_url='', snippet_url='http://example.com' ),
    """Help us share Firefox 4 with the world. <a href="%s">Be a part of Team Firefox!</a>""": 
        dict( icon_url='', snippet_url='http://example.com' ),
    """Everyone's Web is a bit different... What does yours look like? Visualize your Internet at <a href="%s">Webify Me</a>.""": 
        dict( icon_url='', snippet_url='http://example.com' ),
    """Supercharge your Firefox with our <a href="%s">newest collection of add-ons!</a>""": 
        dict( icon_url='', snippet_url='http://example.com' ),
    """The Web belongs to all of us. <a href="%s">Make your mark</a> and show your support for the world's largest public resource.""": 
        dict( icon_url='', snippet_url='http://example.com' ),
    """Celebrate Firefox going mobile with Spark, a free game for Android devices. <a href="%s">Get started</a>.""": 
        dict( icon_url='', snippet_url='http://example.com' ),
}


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
    )

    def handle(self, *args, **options):

        # TODO: Read all of this in from a JSON build file.
        self.bug_id = BUG_ID
        self.rule_description_tmpl = RULE_DESCRIPTION_TMPL
        self.snippet_name_tmpl = SNIPPET_NAME_TMPL
        self.snippet_html_tmpl = SNIPPET_HTML_TMPL
        self.translations_meta = TRANSLATIONS_META

        self.update_locale_rules()
        self.update_snippets()

    def update_locale_rules(self):
        """Ensure a ClientMatchRule exists for each known locale"""
        print "Fetching Firefox product languages"
        self.lang_data = json.load(urllib.urlopen(LANG_JSON_URL))

        print "Updating locale match rules"
        ( rules_created, rules_updated ) = ( [], [] )
        for code, details in self.lang_data.items():

            ( rule, created ) = ClientMatchRule.objects.get_or_create(
                description=self.rule_description_tmpl % dict(
                    name=details['English'], code=code))
            
            # TODO: Read all of this in from a JSON build file.
            rule.version='/4\.0.*/'
            rule.locale=code
            rule.startpage_version = '1'
            rule.name = 'Firefox'
            rule.save()

            if created:
                rules_created.append(code)
            else:
                rules_updated.append(code)

        print "Created: %s" % rules_created
        print "Updated: %s" % rules_updated

        # Built a case-insensitive map of known locale codes.
        self.locales = dict()
        for code, details in self.lang_data.items():
            self.locales[code.lower()] = dict( code=code, name=details['English'] )
        
    def update_snippets(self):
        """Update snippets from bug attachments"""

        print "Fetching data for bug %s" % self.bug_id
        self.bug_data = json.load(urllib.urlopen(BUG_JSON_URL % {'bug_id':self.bug_id}))

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

            print "\n%s\n" % ( locale, )

            # Look up the match rule created earlier for this locale.
            rule = ClientMatchRule.objects.get(
                description=self.rule_description_tmpl % dict(
                    name=locale['name'], code=locale['code']))

            # Attachment data should show up in the JSON as base64. Haven't
            # seen another kind of encoding so far, but we could be surprised.
            if 'base64' == attachment['encoding']:
                data = base64.b64decode(attachment['data'])
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
            for line in data.splitlines():
                line = line.strip()
                # HACK: Some attachments started with UTF-8 marker, so look for that too
                if line.startswith(";") or line.startswith("\xef\xbb\xbf;"):
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
            for english, translated in snippets:
                meta = self.translations_meta[english]
                snippet_html = self.snippet_html_tmpl % dict(
                    icon_url=meta['icon_url'],
                    translation=translated % ( meta['snippet_url'], )
                )

                ( snippet, created ) = Snippet.objects.get_or_create(
                    name=self.snippet_name_tmpl % dict( 
                        bug_id = self.bug_id, 
                        attachment_description = attachment['description'],
                        english = english
                    ))
                snippet.body = snippet_html
                snippet.client_match_rules = [ rule ]
                snippet.save()

                print "\t(%s) %s" % ( ['updated','created'][created], english )

        # Report on bad attachments whose locale or data was unreadable.
        # TODO: Look out for errors in the per-snippet semicolon encoding
        print "BAD: %s" % ( len(bad_attachments) )
