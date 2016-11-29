from django import template

register = template.Library()


@register.simple_tag
def add_query_parameter(request, key, value):
    query_parameters = request.GET.copy()
    query_parameters[key] = value
    return query_parameters.urlencode()
