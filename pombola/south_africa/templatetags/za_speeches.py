from django import template
from django.template import loader, Context

register = template.Library()

@register.assignment_tag()
def section_prev_next_links(section, *args):

    context = Context({
        "next":     get_neighboring_section(section, +1),
        "previous": get_neighboring_section(section, -1),
    })

    t = loader.get_template('speeches/_section_prev_next_links.html')
    return t.render(context)


def get_neighboring_section(section, direction):
    """
    This code is specific to the section hierachy that is used for the
    questions and hansard in the SayIt for ZA.

    This is essentially:

      hansard
      2012
      March
      13
      Some section (has speeches)

     and

       Questions
       Minister of Foo
       16 Oct 2009 (has speeches)

    """

    # These lines lightly modified from https://github.com/mysociety/sayit/blob/master/speeches/models.py#L356-L369
    # 'root' is set to be the section's parent, and s/self/section/, some
    # formatting changes

    if not section.parent:
        return None

    tree = section.parent.get_descendants
    idx = tree.index(section)
    lvl = tree[idx].level
    same_level = [ s for s in tree if s.level == lvl ]
    idx = same_level.index(section)

    if direction == -1 and idx == 0:
        return None

    try:
       return same_level[idx+direction]
    except IndexError:
       return None
