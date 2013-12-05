from django import template

from ..models import Slide


register = template.Library()

@register.assignment_tag
def spinner_random_slide():
    slide = Slide.objects.random_slide()
    return slide
