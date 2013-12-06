from django import template

from ..models import Slide


register = template.Library()

# Commented out as unused, but possibly useful in future
# @register.assignment_tag
# def spinner_random_slide():
#     slide = Slide.objects.random_slide()
#     return slide

@register.assignment_tag
def spinner_active_slides():
    slides = Slide.objects.all().active()
    return slides
