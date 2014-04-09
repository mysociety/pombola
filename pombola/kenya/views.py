# Create your views here.

from pombola.core.views import PersonDetail
from pombola.hansard.views import HansardPersonMixin

class KEPersonDetail(HansardPersonMixin, PersonDetail):

    def get_context_data(self, **kwargs):
        context = super(KEPersonDetail, self).get_context_data(**kwargs)
        context['hansard_entries_to_show'] = ":3"
        return context
