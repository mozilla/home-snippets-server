"""
homesnippets models
"""
import logging
import hashlib
from datetime import datetime
from time import mktime, gmtime
from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
from django.core.cache import cache
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


CACHE_TIMEOUT = getattr(settings, 'SNIPPET_MODEL_CACHE_TIMEOUT')

CACHE_RULE_MATCH_PREFIX       = 'homesnippets_ClientMatchRule_Matches_'
CACHE_RULE_LASTMOD_PREFIX     = 'homesnippets_ClientMatchRule_LastMod_'
CACHE_RULE_ALL_PREFIX         = 'homesnippets_ClientMatchRule_All'
CACHE_RULE_ALL_LASTMOD_PREFIX = 'homesnippets_ClientMatchRule_All_LastMod'
CACHE_RULE_NEW_LASTMOD_PREFIX = 'homesnippets_ClientMatchRule_New_LastMod'
CACHE_SNIPPET_LASTMOD_PREFIX  = 'homesnippets_Snippet_LastMod_'
CACHE_SNIPPET_LOOKUP_PREFIX   = 'homesnippets_Snippet_Lookup_'


def _key_from_client(args):
    plain = '|'.join(['%s=%s'%(k,v) for k,v in args.items()])
    return hashlib.md5(plain).hexdigest()


class ClientMatchRuleManager(models.Manager):
    """Manager for client match rules, allows filtering against match logic"""

    def find_ids_for_matches(self, args):
        cache_key = '%s%s' % (CACHE_RULE_MATCH_PREFIX, _key_from_client(args))
        cache_hit = cache.get(cache_key)

        if cache_hit:
            # If since caching this hit, any of the rules involved were
            # modified or if any new rules were created, invalidate the results.
            lastmod_keys = [
                '%s%s' % (CACHE_RULE_LASTMOD_PREFIX, item)
                for sublist in cache_hit[1] for item in sublist
            ]
            lastmod_keys.append(CACHE_RULE_NEW_LASTMOD_PREFIX)
            lastmods = cache.get_many(lastmod_keys).values()
            newer_lastmods = [ m for m in lastmods if m > cache_hit[0] ]
            if newer_lastmods:
                cache_hit = None

        if not cache_hit:
            # Cache miss, so recalculate the results and cache them.
            matches = [ rule for rule in self._cached_all() 
                    if rule.is_match(args) ]
            (include_ids, exclude_ids) = (
                [str(rule.id) for rule in matches if not rule.exclude],
                [str(rule.id) for rule in matches if rule.exclude],
            )
            cache_hit = (mktime(gmtime()), (include_ids, exclude_ids))
            cache.set(cache_key, cache_hit, CACHE_TIMEOUT)

        return cache_hit[1]

    def _cached_all(self):
        """Cached version of self.all(), invalidated by change to any rule."""
        c_data = cache.get_many([CACHE_RULE_ALL_PREFIX, 
            CACHE_RULE_ALL_LASTMOD_PREFIX])

        lastmod   = c_data.get(CACHE_RULE_ALL_LASTMOD_PREFIX, None)
        cache_hit = c_data.get(CACHE_RULE_ALL_PREFIX, None)

        # Entire cached set gets invalidated if any rule changed.
        if cache_hit and lastmod > cache_hit[0]:
            cache_hit = None

        if not cache_hit:
            cache_hit = ( mktime(gmtime()), self.all() )
            cache.set(CACHE_RULE_ALL_PREFIX, cache_hit, CACHE_TIMEOUT)

        return cache_hit[1]


class ClientMatchRule(models.Model):

    class Meta():
        ordering = ( '-modified', )

    objects = ClientMatchRuleManager()

    description = models.CharField( _('description of rule'),
            null=False, blank=False, default="None", max_length=200)
    exclude = models.BooleanField( _('exclusion rule?'),
            default=False)

    # browser/components/nsBrowserContentHandler.js:911:    
    # const SNIPPETS_URL = "http://snippets.mozilla.com/" + STARTPAGE_VERSION + 
    # "/%NAME%/%VERSION%/%APPBUILDID%/%BUILD_TARGET%/%LOCALE%/%CHANNEL%
    # /%OS_VERSION%/%DISTRIBUTION%/%DISTRIBUTION_VERSION%/";

    startpage_version = models.CharField( _('start page version'), 
            null=True, blank=True, max_length=64)
    name = models.CharField( _('product name'), 
            null=True, blank=True, max_length=64)
    version = models.CharField( _('product version'), 
            null=True, blank=True, max_length=64)
    appbuildid = models.CharField( _('app build id'), 
            null=True, blank=True, max_length=64)
    build_target = models.CharField( _('build target'), 
            null=True, blank=True, max_length=64)
    locale = models.CharField( _('locale'), 
            null=True, blank=True, max_length=64)
    channel = models.CharField( _('channel'), 
            null=True, blank=True, max_length=64)
    os_version = models.CharField( _('os version'), 
            null=True, blank=True, max_length=64)
    distribution = models.CharField( _('distribution'), 
            null=True, blank=True, max_length=64)
    distribution_version = models.CharField( _('distribution version'), 
            null=True, blank=True, max_length=64)
    created = models.DateTimeField( _('date created'), 
            auto_now_add=True, blank=False)
    modified = models.DateTimeField( _('date last modified'), 
            auto_now=True, blank=False)

    def __str__(self):
        fields = ( 'startpage_version', 'name', 'version', 'appbuildid',
            'build_target', 'locale', 'channel', 'os_version',
            'distribution', 'distribution_version', )
        vals = [ getattr(self, field) or '*' for field in fields ]
        return '%s (%s /%s)' % (
            self.description,
            self.exclude and 'EXCLUDE' or 'INCLUDE', 
            '/'.join(vals) 
        )

    def is_match(self, args):
        is_match = True
        for ak,av in args.items():
            mv = getattr(self, ak, None)
            if not mv: 
                continue
            
            if mv.startswith('/'):
                # Regex match
                import re
                try:
                    p = re.compile(mv[1:-1])
                    if p.match(av) is None:
                        is_match = False
                except re.error:
                    # TODO: log error? validate regex in form submit?
                    is_match = False

            elif av != mv:
                # Exact match
                is_match = False

        return is_match


def rule_update_lastmods(sender, instance, created=False, **kwargs):
    """On a change to a rule, bump lastmod timestamps for that rule and the set
    of all cached rules."""
    now = mktime(gmtime())
    lastmods = {
        # Timestamp for this rule.
        '%s%s' % (CACHE_RULE_LASTMOD_PREFIX, instance.id): now,
        # Timestamp for set of all rules.
        CACHE_RULE_ALL_LASTMOD_PREFIX: now,
    }
    if created:
        # Update timestamp since last new rule created.
        lastmods[CACHE_RULE_NEW_LASTMOD_PREFIX] = now
    cache.set_many(lastmods, CACHE_TIMEOUT)

post_save.connect(rule_update_lastmods, sender=ClientMatchRule)
post_delete.connect(rule_update_lastmods, sender=ClientMatchRule)


class SnippetManager(models.Manager):

    def find_snippets_with_match_rules(self, args, time_now=None):
        """Find snippets data using match rules. 

        Returned is a list of dicts with id and body of snippets found, rather
        than full Snippet model objects. This makes things easier to cache - 
        if full snippets are required, try using the id's to look them up.
        """
        if time_now is None:
            time_now = datetime.now()

        preview = ( 'preview' in args ) and args['preview']
        include_ids, exclude_ids = \
            ClientMatchRule.objects.find_ids_for_matches(args)
        snippets = self.find_snippets_for_rule_ids(preview, include_ids, exclude_ids)

        # Filter for date ranges here, rather than in SQL. 
        #
        # This is a compromise to make snippet match results more cacheable -
        # ie. cached data should only be recalculated in response to content
        # changes, not the passage of time.
        snippets_data = [ s for s in snippets if ( 
            ( not s['pub_start'] or time_now >= s['pub_start'] ) and
            ( not s['pub_end']   or time_now <  s['pub_end'] ) 
        ) ]

        return snippets_data

    def find_snippets_for_rule_ids(self, preview, include_ids, exclude_ids):
        """Given a set of matching inclusion & exclusion rule IDs, look up the
        corresponding snippets."""

        if not include_ids and not exclude_ids: 
            return []

        # Could base the cache key on the entire text of the SQL query
        # constructed below, but we might someday use something other than a DB
        # for persistence.
        cache_key = '%s%s' % ( CACHE_SNIPPET_LOOKUP_PREFIX, hashlib.md5(
            'include:%s;exclude:%s;preview:%s' % (
                ','.join(include_ids), ','.join(exclude_ids), preview)
        ).hexdigest() )
        cache_hit = cache.get(cache_key)

        if cache_hit:
            # Invalidate if any of the lastmods of related rules, snippets, or
            # new rule creation is newer than the cache
            keys = [ '%s%s' % (CACHE_RULE_LASTMOD_PREFIX, item)
                for sublist in cache_hit[1] for item in sublist ]
            keys.extend([ '%s%s' % (CACHE_SNIPPET_LASTMOD_PREFIX, item['id'])
                for item in cache_hit[2] ])
            keys.append(CACHE_RULE_NEW_LASTMOD_PREFIX)
            lastmods = cache.get_many(keys).values()
            newer_lastmods = [ m for m in lastmods if m > cache_hit[0] ]
            if newer_lastmods:
                cache_hit = None

        if not cache_hit:
            # No cache hit, look up the snippets associated with rules.
            sql_base = """
                SELECT homesnippets_snippet.* 
                FROM homesnippets_snippet
                WHERE ( %s )
                ORDER BY priority, pub_start, modified
            """
            where = [
                '( homesnippets_snippet.disabled <> 1 )',
            ]
            if not preview:
                where.append('( homesnippets_snippet.preview <> 1 )')
            if include_ids:
                where.append(""" 
                    homesnippets_snippet.id IN (
                        SELECT snippet_id
                        FROM homesnippets_snippet_client_match_rules
                        WHERE clientmatchrule_id IN (%s)
                    ) 
                """ % ",".join(include_ids))
            if exclude_ids:
                where.append(""" 
                    homesnippets_snippet.id NOT IN (
                        SELECT snippet_id
                        FROM homesnippets_snippet_client_match_rules
                        WHERE clientmatchrule_id IN (%s)
                    ) 
                """ % ",".join(exclude_ids))
            sql = sql_base % (' AND '.join(where))

            # Reduce snippet model objects to more cacheable dicts
            snippet_objs = self.raw(sql)
            snippets = [ 
                dict(
                    id=snippet.id, 
                    name=snippet.name,
                    body=snippet.body,
                    pub_start=snippet.pub_start,
                    pub_end=snippet.pub_end,
                )
                for snippet in snippet_objs
            ]
            cache_hit = ( mktime(gmtime()), (include_ids, exclude_ids), snippets, )
            cache.set(cache_key, cache_hit, CACHE_TIMEOUT)

        return cache_hit[2]


class Snippet(models.Model):

    class Meta():
        ordering = ( '-modified', '-pub_start', '-priority' )

    objects = SnippetManager()

    client_match_rules = models.ManyToManyField(
            ClientMatchRule, blank=False)
    
    name = models.CharField( _("short name (only shown to admins)"), 
            blank=False, max_length=80)
    body = models.TextField( _("content body"), 
            blank=False)

    priority = models.IntegerField( _('sort order priority'),
            default=0, blank=True, null=True)
    disabled = models.BooleanField( _('disabled?'),
            default=False)
    preview = models.BooleanField( _('preview only?'),
            default=False)
    pub_start = models.DateTimeField( _('display start time'),
            blank=True, null=True) 
    pub_end = models.DateTimeField( _('display end time'),
            blank=True, null=True) 

    created = models.DateTimeField( _('date created'), 
            auto_now_add=True, blank=False)
    modified = models.DateTimeField( _('date last modified'), 
            auto_now=True, blank=False)

    
def snippet_update_lastmod(sender, instance, **kwargs):
    """On a change to a snippet, bump its cached lastmod timestamp"""
    now = mktime(gmtime())
    lastmods = {
        '%s%s' % (CACHE_SNIPPET_LASTMOD_PREFIX, instance.id): now,
    }
    for rule in instance.client_match_rules.all():
        lastmods['%s%s' % (CACHE_RULE_LASTMOD_PREFIX, rule.id)] = now
    cache.set_many(lastmods, CACHE_TIMEOUT)

post_save.connect(snippet_update_lastmod, sender=Snippet)
post_delete.connect(snippet_update_lastmod, sender=Snippet)

