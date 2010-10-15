from django.contrib import admin

from homesnippets.models import Snippet, ClientMatchRule

class ClientMatchRuleAdmin(admin.ModelAdmin):
    pass

admin.site.register(ClientMatchRule, ClientMatchRuleAdmin)

class SnippetAdmin(admin.ModelAdmin):
    fields = ['name', 'body', 'client_match_rules' ]
    list_display = ( 'name', 'modified' )

admin.site.register(Snippet, SnippetAdmin)
