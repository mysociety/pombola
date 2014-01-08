import datetime

from django import template
from speeches.models import Section

register = template.Library()

# NOTE: this code is far from ideal. Sharing it with others in a pull request
# to get opinions about how to improve.

# TODO:
# - cache results of min_speech_datetime and section_prev_next_links (both of
#   which will be called multiple times with same input)

@register.inclusion_tag('speeches/_section_prev_next_links.html')
def section_prev_next_links(section):

    return {
        "next":     get_neighboring_section(section, +1),
        "previous": get_neighboring_section(section, -1),
    }

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
    except:
       return None
