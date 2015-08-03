from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect

from .models import SlugRedirect

def get_slug_redirect(model, slug):
    try:
        sr = SlugRedirect.objects.get(
            content_type=ContentType.objects.get_for_model(model),
            old_object_slug=slug
        )
        return sr.new_object
    except SlugRedirect.DoesNotExist:
        return None


class SlugRedirectMixin(object):
    """Adds SlugRedirect redirection for DetailView-derived classes"""

    def redirect_to(self, correct_object):
        return redirect(correct_object)

    def get(self, request, *args, **kwargs):
        # Check if this is an old slug for redirection:
        slug = kwargs['slug']
        object_to_redirect_to = get_slug_redirect(self.model, slug)
        if object_to_redirect_to:
            return self.redirect_to(object_to_redirect_to)
        # Otherwise look up the slug as normal:
        else:
            return super(SlugRedirectMixin, self).get(request, *args, **kwargs)
