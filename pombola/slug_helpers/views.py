from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect

from .models import SlugRedirect

class SlugRedirectMixin(object):
    """Adds SlugRedirect redirection for DetailView-derived classes"""

    def redirect_to(self, correct_object):
        return redirect(correct_object)

    def get(self, request, *args, **kwargs):
        # Check if this is old slug for redirection:
        slug = kwargs['slug']
        try:
            sr = SlugRedirect.objects.get(
                content_type=ContentType.objects.get_for_model(self.model),
                old_object_slug=slug
            )
            return self.redirect_to(sr.new_object)
        # Otherwise look up the slug as normal:
        except SlugRedirect.DoesNotExist:
            return super(SlugRedirectMixin, self).get(request, *args, **kwargs)
