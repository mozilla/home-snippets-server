from django.contrib import admin

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
    fields = ( 
        'name', 'body', 
        'client_match_rules', 
        'preview', 'disabled',
        'priority', 'pub_start', 'pub_end', 
    )
    list_display = ( 
        'name', 'id',
        'preview', 'disabled',
        'priority', 'pub_start', 'pub_end',
        'modified' 
    )

admin.site.register(Snippet, SnippetAdmin)
