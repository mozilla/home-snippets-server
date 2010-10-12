from django.db import models

from django.contrib.sites.models import Site
from django.contrib.auth.models import User

from django.utils.translation import ugettext_lazy as _


class Snippet(models.Model):
    name = models.CharField(_("name for snippet (not displayed)"), 
            blank=False, max_length=80)
    body = models.TextField(_("snippet content body"), 
            blank=False)
    created = models.DateTimeField(_('date created'), 
            auto_now_add=True)
    modified = models.DateTimeField(_('date last modified'), 
            auto_now=True)

