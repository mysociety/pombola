
from django.views.generic import ListView, TemplateView


class SearchPollUnitNumberView(TemplateView):
    template_name = 'search/poll-unit-number.html'
