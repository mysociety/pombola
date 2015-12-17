from django.template import Library, Node, TemplateSyntaxError, Variable

register = Library()

@register.tag
def maybehidden(parser, token):
    """Link text to the person if they're non-hidden or the user's a superuser

    For example:

        {% maybehidden person user %}
            ...
        {% endmaybehidden %}

    Or if you don't want the special case that a superuser can see the
    link anyway, you can leave out the user:

        {% maybehidden person %}
            ...
        {% endmaybehidden %}
    """
    return do_maybehidden(parser, token)

def do_maybehidden(parser, token):
    bits = list(token.split_contents())
    if len(bits) not in (2, 3):
        raise TemplateSyntaxError("%r takes one or two arguments" % bits[0])
    end_tag = 'end' + bits[0]
    nodelist = parser.parse((end_tag,))
    parser.delete_first_token()
    person = bits[1]
    if len(bits) == 3:
        user = bits[2]
    else:
        user = None
    return MaybeHiddenNode(person, user, nodelist)

class MaybeHiddenNode(Node):

    def __init__(self, person, user, nodelist):
        self.person = Variable(person)
        self.user = Variable(user) if user else None
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)

        # Resolve the variables in the context that's being rendered:
        user = None
        if user:
            user = self.user.resolve(context)
        person = self.person.resolve(context)

        # Now wrap the output in a link to the person page if the user
        # is a super user or if not, only if the person is not hidden:
        if (user and user.is_superuser) or not person.hidden:
            return u'<a href="{url}">{enclosed_html}</a>'.format(
                url=person.get_absolute_url(),
                enclosed_html=output)
        else:
            return output
