"""
"""
import logging

from django.db import models

from django.contrib.sites.models import Site
from django.contrib.auth.models import User

from django.utils.translation import ugettext_lazy as _


class ClientMatchRuleManager(models.Manager):

    def filter_for_matches(self, args):

        # TODO: Need some heavy caching here.
        # MD5 of normalized args as a cache key?

        return [ rule for rule in self.all() if rule.is_match(args) ]

    
class ClientMatchRule(models.Model):

    objects = ClientMatchRuleManager()

    class Meta():
        ordering = ('priority',)

    priority = models.IntegerField(
            _('priority sort order'),
            default=0, blank=True)
    exclude = models.BooleanField(
            _('exclusion rule?'),
            default=False)

    # browser/components/nsBrowserContentHandler.js:911:    const SNIPPETS_URL = "http://snippets.mozilla.com/" + STARTPAGE_VERSION + "/%NAME%/%VERSION%/%APPBUILDID%/%BUILD_TARGET%/%LOCALE%/%CHANNEL%/%OS_VERSION%/%DISTRIBUTION%/%DISTRIBUTION_VERSION%/";

    startpage_version = models.CharField(
            _('start page version'), 
            null=True, blank=True, max_length=64, default='1')
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

    def is_match(self, args):
        is_match = True
        for ak,av in args.items():
            mv = getattr(self, ak, None)
            if not mv: 
                continue
            if av != mv:
                is_match = False
        return is_match


class SnippetManager(models.Manager):

    def filter_by_match_rules(self, args):

        # TODO: Need some heavy caching here.
        # TODO: Need to get the table names from respective models?
        # MD5 of normalized args as a cache key?

        matching_rules = ClientMatchRule.objects.filter_for_matches(args)
        if not matching_rules: return ()

        where = []

        include_ids = ",".join([ str(rule.id) 
            for rule in matching_rules if not rule.exclude ])

        if include_ids:
            where.append(""" "homesnippets_snippet"."id" IN (
                SELECT "snippet_id"
                FROM "homesnippets_snippet_client_match_rules"
                WHERE "clientmatchrule_id" IN (%s)
            ) """ % include_ids)

        exclude_ids = ",".join([ str(rule.id) 
            for rule in matching_rules if rule.exclude ])

        if exclude_ids:
            where.append(""" "homesnippets_snippet"."id" NOT IN (
                SELECT "snippet_id"
                FROM "homesnippets_snippet_client_match_rules"
                WHERE "clientmatchrule_id" IN (%s)
            ) """ % exclude_ids)

        sql = """
            SELECT DISTINCT "homesnippets_snippet".* 
            FROM "homesnippets_snippet"
            WHERE ( %s )
        """ % ' AND '.join(where)

        snippets = self.raw(sql)
        return snippets

    
class Snippet(models.Model):

    objects = SnippetManager()

    class Meta():
        ordering = ('pub_start', 'modified', )

    client_match_rules = models.ManyToManyField(
            ClientMatchRule, blank=True)
    
    name = models.CharField(
            _("name for snippet (not displayed)"), 
            blank=False, max_length=80)
    body = models.TextField(
            _("snippet content body"), 
            blank=False)
    
    pub_start = models.DateTimeField(
            _('time from which snippet start being served (optional)'),
            blank=True, null=True) 
    pub_end = models.DateTimeField(
            _('time after which snippet should stop being served (optional)'),
            blank=True, null=True) 
    
    created = models.DateTimeField(
            _('date created'), 
            auto_now_add=True, blank=False)
    modified = models.DateTimeField(
            _('date last modified'), 
            auto_now=True, blank=False)

    
