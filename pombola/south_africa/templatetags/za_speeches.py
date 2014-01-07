from django import template

register = template.Library()

@register.inclusion_tag('speeches/_section_prev_next_links.html')
def section_prev_next_links(section):
    next_section = section.get_next_node()
    prev_section = section.get_previous_node()

    return {
        "next":     next_section,
        "previous": prev_section,
    }
