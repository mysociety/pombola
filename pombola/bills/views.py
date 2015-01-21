from django.http import Http404
from django.utils.functional import cached_property
from django.views.generic import TemplateView, ListView
from django.db.models import Count

from pombola.core.models import ParliamentarySession
from pombola.bills.models import Bill



class IndexView(TemplateView):
    template_name = "bills/index.html"

    @cached_property
    def parliamentary_sessions(self):
        return ParliamentarySession.objects.annotate(Count("bill")).filter(bill__count__gt=0)


class BillListView(ListView):
    model = Bill
    paginate_by = 50

    def get_queryset(self):
        base_qs = super(BillListView, self).get_queryset()
        session = self.parliamentary_session
        return base_qs.filter(parliamentary_session=session)

    @cached_property
    def parliamentary_session(self):
        slug = self.kwargs.get("session_slug")
        try:
            session = ParliamentarySession.objects.get(slug=slug)
        except ParliamentarySession.DoesNotExist:
            raise Http404
        return session
