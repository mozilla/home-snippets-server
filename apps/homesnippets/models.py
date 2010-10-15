"""
homesnippets models
"""
import logging
import hashlib
from time import mktime, gmtime
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.core.cache import cache
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


CACHE_TIMEOUT = getattr(settings, 'SNIPPET_MODEL_CACHE_TIMEOUT')

CACHE_RULE_MATCH_PREFIX = 'ClientMatchRule_Matches_'
CACHE_RULE_LASTMOD_PREFIX = 'ClientMatchRule_LastMod_'
CACHE_SNIPPET_MATCH_PREFIX = 'Snippet_Matches_'
CACHE_SNIPPET_LASTMOD_PREFIX = 'Snippet_LastMod_'


def _key_from_client(args):
    plain = '|'.join(['%s=%s'%(k,v) for k,v in args.items()])
    return hashlib.md5(plain).hexdigest()


class ClientMatchRuleManager(models.Manager):
    """Manager for client match rules, allows filtering against match logic"""

    def find_ids_for_matches(self, args):
        cache_key = '%s%s' % (CACHE_RULE_MATCH_PREFIX, _key_from_client(args))
        cache_hit = cache.get(cache_key)

        if cache_hit:
            # Look to see if any rule involved in this cache hit has been
            # changed since the match results were cached. If so, discard the
            # cache hit.
            lastmods = cache.get_many([
                '%s%s' % (CACHE_RULE_LASTMOD_PREFIX, item)
                for sublist in cache_hit[1] for item in sublist
            ]).values()
            newer_lastmods = [ m for m in lastmods if m > cache_hit[0] ]
            if newer_lastmods:
                cache_hit = None

        if not cache_hit:
            # Cache miss, so recalculate the results and cache them.
            matches = [ rule for rule in self.all() if rule.is_match(args) ]
            (include_ids, exclude_ids) = (
                [str(rule.id) for rule in matches if not rule.exclude],
                [str(rule.id) for rule in matches if rule.exclude],
            )
            cache_hit = (mktime(gmtime()), (include_ids, exclude_ids))
            cache.set(cache_key, cache_hit, CACHE_TIMEOUT)

        return cache_hit[1]


class ClientMatchRule(models.Model):

    class Meta():
        ordering = ( '-modified', )

    objects = ClientMatchRuleManager()

    description = models.TextField(
            _('description of the intent behind this rule'),
            null=False, blank=False, default="None")
    exclude = models.BooleanField(
            _('exclusion rule?'),
            default=False)

    # browser/components/nsBrowserContentHandler.js:911:    
    # const SNIPPETS_URL = "http://snippets.mozilla.com/" + STARTPAGE_VERSION + 
    # "/%NAME%/%VERSION%/%APPBUILDID%/%BUILD_TARGET%/%LOCALE%/%CHANNEL%
    # /%OS_VERSION%/%DISTRIBUTION%/%DISTRIBUTION_VERSION%/";

    startpage_version = models.CharField(
            _('start page version'), 
            null=True, blank=True, max_length=64)
    name = models.CharField(
            _('product name'), 
            null=True, blank=True, max_length=64)
    version = models.CharField(
            _('product version'), 
            null=True, blank=True, max_length=64)
    appbuildid = models.CharField(
            _('app build id'), 
            null=True, blank=True, max_length=64)
    build_target = models.CharField(
            _('build target'), 
            null=True, blank=True, max_length=64)
    locale = models.CharField(
            _('locale'), 
            null=True, blank=True, max_length=64)
    channel = models.CharField(
            _('channel'), 
            null=True, blank=True, max_length=64)
    os_version = models.CharField(
            _('os version'), 
            null=True, blank=True, max_length=64)
    distribution = models.CharField(
            _('distribution'), 
            null=True, blank=True, max_length=64)
    distribution_version = models.CharField(
            _('distribution version'), 
            null=True, blank=True, max_length=64)
    created = models.DateTimeField(
            _('date created'), 
            auto_now_add=True, blank=False)
    modified = models.DateTimeField(
            _('date last modified'), 
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


def rule_update_lastmod(sender, instance, **kwargs):
    now = mktime(gmtime())
    cache.set('%s%s' % (CACHE_RULE_LASTMOD_PREFIX, instance.id), 
            now, CACHE_TIMEOUT)
post_save.connect(rule_update_lastmod, sender=ClientMatchRule)
    

class SnippetManager(models.Manager):

    def filter_by_match_rules(self, args):
        # TODO: Need to get the table names from respective models?
        cache_key = '%s%s' % (CACHE_SNIPPET_MATCH_PREFIX, _key_from_client(args))
        cache_hit = cache.get(cache_key)

        if cache_hit:
            # Gather up the last modified timestamps of all snippets and rules
            # involved in the cached results. If any of them is newer than the
            # timestamp of the cache results, discard the cache hit as invalid.
            keys = [ '%s%s' % (CACHE_RULE_LASTMOD_PREFIX, item)
                for sublist in cache_hit[1] for item in sublist ]
            keys.extend([ '%s%s' % (CACHE_SNIPPET_LASTMOD_PREFIX, item.id)
                for item in cache_hit[2] ])
            lastmods = cache.get_many(keys).values()
            newer_lastmods = [ m for m in lastmods if m > cache_hit[0] ]
            if newer_lastmods:
                cache_hit = None

        if not cache_hit:

            include_ids, exclude_ids = \
                ClientMatchRule.objects.find_ids_for_matches(args)

            if not include_ids and not exclude_ids: 
                snippets = []

            else:
                sql = """
                    SELECT "homesnippets_snippet".* 
                    FROM "homesnippets_snippet"
                    WHERE ( %s )
                """
                where = []
                if include_ids:
                    where.append(""" 
                        "homesnippets_snippet"."id" IN (
                            SELECT "snippet_id"
                            FROM "homesnippets_snippet_client_match_rules"
                            WHERE "clientmatchrule_id" IN (%s)
                        ) 
                    """ % ",".join(include_ids))
                if exclude_ids:
                    where.append(""" 
                        "homesnippets_snippet"."id" NOT IN (
                            SELECT "snippet_id"
                            FROM "homesnippets_snippet_client_match_rules"
                            WHERE "clientmatchrule_id" IN (%s)
                        ) 
                    """ % ",".join(exclude_ids))
                snippets = self.raw(sql % (' AND '.join(where))) 

            cache_hit = (mktime(gmtime()), (include_ids, exclude_ids), snippets)
            cache.set(cache_key, cache_hit, CACHE_TIMEOUT)

        return cache_hit[2]


class Snippet(models.Model):

    class Meta():
        ordering = ( '-modified', )

    objects = SnippetManager()

    client_match_rules = models.ManyToManyField(
            ClientMatchRule, blank=True)
    
    name = models.CharField(
            _("name for snippet (not displayed)"), 
            blank=False, max_length=80)
    body = models.TextField(
            _("snippet content body"), 
            blank=False)
    created = models.DateTimeField(
            _('date created'), 
            auto_now_add=True, blank=False)
    modified = models.DateTimeField(
            _('date last modified'), 
            auto_now=True, blank=False)

    
def snippet_update_lastmod(sender, instance, **kwargs):
    now = mktime(gmtime())
    cache.set('%s%s' % (CACHE_SNIPPET_LASTMOD_PREFIX, instance.id), 
            now, CACHE_TIMEOUT)
post_save.connect(snippet_update_lastmod, sender=Snippet)

