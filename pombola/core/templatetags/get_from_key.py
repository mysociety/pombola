from django import template

register = template.Library()


@register.filter
def get_from_key(value, arg):
    try:
        return value[arg]
    except KeyError:
        return ''
