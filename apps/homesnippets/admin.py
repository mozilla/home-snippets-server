from datetime import datetime

from django import forms
from django.contrib import admin, messages
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django.utils.encoding import smart_unicode
from django.utils.safestring import mark_safe

from smuggler.settings import SMUGGLER_FORMAT
from smuggler.utils import serialize_to_response

from homesnippets.models import Snippet, ClientMatchRule


def dump_selected(modeladmin, request, queryset):
    """Produce a smuggler dump for a selected set of model objects"""
    objects = queryset.all()
    filename = '%s-%s_%s.%s' % ('homesnippets', modeladmin.dump_name,
                                datetime.now().isoformat(), SMUGGLER_FORMAT)
    response = HttpResponse(mimetype="text/plain")
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return serialize_to_response(objects, response)

dump_selected.short_description = "Dump selected objects as JSON data"


def dump_selected_snippets(modeladmin, request, queryset):
    """Produce a smuggler dump for a selected set of snippets, along with
    associated client match rules."""
    snippets = queryset.all()

    # Assemble a unique set of client match rules used by selected snippets.
    rules = dict()
    for s in snippets:
        for rule in s.client_match_rules.all():
            rules[rule.pk] = rule

    # Combine set of rules and snippets for output
    objects = rules.values() + list(snippets)

    filename = '%s-%s_%s.%s' % ('homesnippets', 'snippets',
                                datetime.now().isoformat(), SMUGGLER_FORMAT)
    response = HttpResponse(mimetype="text/plain")
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return serialize_to_response(objects, response)

dump_selected_snippets.short_description = "Dump selected snippets (and " \
                                           "client match rules) as JSON data"


def disable_selected_snippets(modeladmin, request, queryset):
    cnt = 0
    for snippet in queryset.all():
        snippet.disabled = True
        snippet.save()
        cnt += 1
    messages.add_message(request, messages.INFO,
            ('%(cnt)d snippet(s) disabled') % dict(cnt=cnt))

disable_selected_snippets.short_description = "Disable selected snippets"


def enable_selected_snippets(modeladmin, request, queryset):
    cnt = 0
    for snippet in queryset.all():
        snippet.disabled = False
        snippet.save()
        cnt += 1
    messages.add_message(request, messages.INFO,
            ('%(cnt)d snippet(s) enabled') % dict(cnt=cnt))

enable_selected_snippets.short_description = "Enable selected snippets"


def bulk_edit_dates(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    url = '%s?ids=%s' % (reverse('admin_bulk_date_change'), ','.join(selected))
    return HttpResponseRedirect(url)

bulk_edit_dates.short_description = "Edit start and end dates of selected " \
                                    "snippets"


class ClientMatchRuleAdmin(admin.ModelAdmin):
    change_list_template = 'smuggler/change_list.html'

    actions = [dump_selected]
    dump_name = 'clientmatchrules'

    list_per_page = 250

    list_display = (
        'description',
        'related_snippets',
        'exclude',
        'startpage_version', 'name', 'version',
        'locale',
        'appbuildid', 'build_target',
        'channel', 'os_version', 'distribution', 'distribution_version',
        'modified',
    )

    list_editable = (
    )

    list_filter = (
        'name', 'version', 'os_version',
        'appbuildid', 'build_target', 'channel', 'distribution',
        'locale',
    )

admin.site.register(ClientMatchRule, ClientMatchRuleAdmin)


class SnippetBodyWidget(forms.Textarea):
    class Media:
        css = {
            'all': ('snippetBodyWidget.css',)
        }
        js = ('jquery-1.6.1.min.js', 'jquery.easytabs.min.js',
              'snippetBodyWidget.js')

    def render(self, name, value, attrs=None):
        textarea = super(SnippetBodyWidget, self).render(name, value, attrs)
        widget = render_to_string('snippetBodyWidget.html',
                                  {"textarea": textarea})
        return mark_safe(smart_unicode(widget))


class SnippetAdmin(admin.ModelAdmin):
    change_list_template = 'smuggler/change_list.html'

    actions = [
        dump_selected_snippets,
        disable_selected_snippets,
        enable_selected_snippets,
        bulk_edit_dates,
    ]
    dump_name = 'snippets'

    save_on_top = True
    actions_on_bottom = True

    search_fields = (
        'client_match_rules__description',
        'name', 'body',
    )

    list_filter = (
        'pub_start',
        'pub_end',
        'client_match_rules',
    )

    fields = (
        'name', 'body',
        'preview', 'disabled',
        'priority', 'pub_start', 'pub_end',
        'client_match_rules',
    )

    list_per_page = 250

    list_display = (
        'name',
        'disabled',
        'priority', 'pub_start', 'pub_end',
        'modified'
    )

    list_links = (
        'name',
    )

    list_editable = (
        'disabled', 'priority',
        'pub_start', 'pub_end',
    )

    filter_horizontal = ('client_match_rules',)

    formfield_overrides = {
        models.ManyToManyField: {
            "widget": forms.widgets.SelectMultiple(attrs={"size": 50})
        }
    }

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'body':
            kwargs['widget'] = SnippetBodyWidget
        return super(SnippetAdmin, self).formfield_for_dbfield(db_field,
                                                               **kwargs)

admin.site.register(Snippet, SnippetAdmin)
