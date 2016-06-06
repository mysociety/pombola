from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from mapit.models import Area, Generation

from .election_data_2017.iebc_offices import IEBC_OFFICE_DATA
from .forms import ConstituencyGroupedByCountySelectForm


AREA_ID_TO_OFFICE = {
    o['cons_id']: o
    for o in IEBC_OFFICE_DATA
}


class OfficeSingleSelectView(TemplateView):

    template_name = 'iebc_office_single_select.html'

    def get_context_data(self, **kwargs):
        context = super(OfficeSingleSelectView, self).get_context_data(**kwargs)
        context['form_counties'] = ConstituencyGroupedByCountySelectForm()
        return context


class OfficeDetailView(TemplateView):

    template_name = 'iebc_office_detail.html'

    def get(self, request, *args, **kwargs):
        area_id = request.GET.get('area')
        generation = Generation.objects.current()

        if not area_id:
            return HttpResponseRedirect(reverse('iebc-offices-single-select'))

        self.area = get_object_or_404(
            Area.objects.filter(
                generation_low__lte=generation,
                generation_high__gte=generation,
                type__code='CON',
            ),
            pk=area_id
        )
        return super(OfficeDetailView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(OfficeDetailView, self).get_context_data(**kwargs)
        context['area'] = self.area
        context['office'] = AREA_ID_TO_OFFICE.get(self.area.id)
        return context
