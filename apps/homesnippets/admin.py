from django.contrib import admin

from homesnippets.models import Snippet, ClientMatchRule

class ClientMatchRuleAdmin(admin.ModelAdmin):
    change_list_template = 'smuggler/change_list.html'
    pass

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
        'name', 
        'preview', 'disabled',
        'priority', 'pub_start', 'pub_end',
        'modified' 
    )

admin.site.register(Snippet, SnippetAdmin)
