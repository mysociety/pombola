# Create your views here.

from pombola.core.views import PersonDetail, PersonDetailSub
from pombola.hansard.views import HansardPersonMixin

class KEPersonDetail(HansardPersonMixin, PersonDetail):

    def get_context_data(self, **kwargs):
        context = super(KEPersonDetail, self).get_context_data(**kwargs)
        context['hansard_entries_to_show'] = ":3"
        return context

class KEPersonDetailAppearances(HansardPersonMixin, PersonDetailSub):

    def get_context_data(self, **kwargs):
        context = super(KEPersonDetailAppearances, self).get_context_data(**kwargs)
        context['hansard_entries_to_show'] = ":5"
        context['lifetime_summary'] = context['hansard_entries'] \
            .monthly_appearance_counts()
        return context
