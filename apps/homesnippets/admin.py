from django.contrib import admin

from homesnippets.models import Snippet

class SnippetAdmin(admin.ModelAdmin):
    fields = ['name', 'body']
    list_display = ( 'name', 'modified' )

admin.site.register(Snippet, SnippetAdmin)
