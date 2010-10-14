from django.contrib import admin

from homesnippets.models import Snippet, ClientMatchRule

class ClientMatchRuleAdmin(admin.ModelAdmin):
    pass

admin.site.register(ClientMatchRule, ClientMatchRuleAdmin)

class SnippetAdmin(admin.ModelAdmin):
    fields = ['name', 'body', 'pub_start', 'pub_end', 'client_match_rules' ]
    list_display = ( 'name', 'pub_start', 'pub_end', 'modified' )

admin.site.register(Snippet, SnippetAdmin)
