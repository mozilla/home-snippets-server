from django.contrib import admin
from django import forms
from django.db import models

from homesnippets.models import Snippet, ClientMatchRule

class ClientMatchRuleAdmin(admin.ModelAdmin):
    change_list_template = 'smuggler/change_list.html'

    list_per_page = 250

    list_display = (
        'description',
        'related_snippets',
        'exclude',
        'startpage_version', 'name', 'version', 
        'locale',
        'appbuildid', 'build_target', 
        'channel', 'os_version', 'distribution', 'distribution_version',
        'created', 'modified',
    )

    list_editable = (
    )

    list_filter = (
        'name', 'version', 'os_version', 
        'appbuildid', 'build_target', 'channel', 'distribution',
        'locale', 
    )

admin.site.register(ClientMatchRule, ClientMatchRuleAdmin)

class SnippetAdmin(admin.ModelAdmin):
    change_list_template = 'smuggler/change_list.html'
    
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
        'preview', 'disabled',
        'priority', 'pub_start', 'pub_end',
        'modified' 
    )

    list_links = (
        'name',
    )

    list_editable = (
        'preview', 'disabled', 'priority',
        'pub_start', 'pub_end',
    )

    filter_horizontal = ( 'client_match_rules', )

    formfield_overrides = {
        models.ManyToManyField: {
            "widget": forms.widgets.SelectMultiple(attrs={"size":50})
        }
    }

admin.site.register(Snippet, SnippetAdmin)
