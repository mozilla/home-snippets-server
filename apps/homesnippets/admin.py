from django.contrib import admin
from django import forms
from django.db import models

from homesnippets.models import Snippet, ClientMatchRule

class ClientMatchRuleAdmin(admin.ModelAdmin):
    change_list_template = 'smuggler/change_list.html'
    list_display = (
        'description',
        'id', 'exclude',
        'startpage_version', 'name', 'locale',
        'version', 'appbuildid', 'build_target', 
        'channel', 'os_version', 'distribution', 'distribution_version',
        'created', 'modified',
    )

admin.site.register(ClientMatchRule, ClientMatchRuleAdmin)

class SnippetAdmin(admin.ModelAdmin):
    change_list_template = 'smuggler/change_list.html'
    
    save_on_top = True
    actions_on_bottom = True

    fields = ( 
        'name', 'body', 
        'preview', 'disabled',
        'priority', 'pub_start', 'pub_end', 
        'client_match_rules', 
    )
    
    list_display = ( 
        'name', 'id',
        'preview', 'disabled',
        'priority', 'pub_start', 'pub_end',
        'modified' 
    )

    formfield_overrides = {
        models.ManyToManyField: {
            "widget": forms.widgets.SelectMultiple(attrs={"size":50})
        }
    }

admin.site.register(Snippet, SnippetAdmin)
