from django.views.generic.base import TemplateView

from .forms import CountyPerformancePetitionForm

class CountyPerformanceView(TemplateView):
    """This view displays a page about county performance with calls to action"""

    template_name = 'county-performance.html'

    def get_context_data(self, **kwargs):
        context = super(CountyPerformanceView, self).get_context_data(**kwargs)
        context['suppress_banner'] = True
        context['petition_form'] = CountyPerformancePetitionForm()
        return context
