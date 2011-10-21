from django import template

register = template.Library()


SYMBOLS = [
    ('[[[', '{{{'),
    (']]]', '}}}'),
    ('[[', '{{'),
    (']]', '}}'),
]


@register.tag
def icanhaz(parser, token):
    """Replaces double and triple square brackets with curly brackets.

    Used for embedding ICanHaz/Mustache templates in django templates.
    """
    nodelist = parser.parse(('endicanhaz',))
    parser.delete_first_token()
    return ICanHazNode(nodelist)


class ICanHazNode(template.Node):
    """Parses template code and replaces certain symbols."""
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        for find, replace in SYMBOLS:
            output = output.replace(find, replace)
        return output
