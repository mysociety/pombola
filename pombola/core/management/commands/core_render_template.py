from django.core.management.base import LabelCommand
from django.template.loader import render_to_string
from django.template import RequestContext
from django.http import HttpRequest

class Command(LabelCommand):
    help = 'Render a template to STDOUT'
    args = '<template path>'

    def handle_label(self, template_path, **options):


        # create a minimal fake request and request context
        request = HttpRequest()
        request.META = {
            "SERVER_NAME": 'fake',
            "SERVER_PORT": 80,
        }
        request_context = RequestContext(request)

        print render_to_string(template_path, {}, request_context)
