from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.conf import settings
from django.core.cache import cache

from mapit.models import Area, Generation

from .election_data_2017.iebc_offices import IEBC_OFFICE_DATA
from .forms import ConstituencyGroupedByCountySelectForm

import requests


AREA_ID_TO_OFFICE = {
    o['cons_id']: o
    for o in IEBC_OFFICE_DATA
}


class TreatmentPlacebo(TemplateView):

    template_name = 'facebook-experiment-placebo.html'

    def get(self, request, *args, **kwargs):
        self.survey_session = request.GET.get('sid')

        return super(TreatmentPlacebo, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TreatmentPlacebo, self).get_context_data(**kwargs)
        context['sid'] = self.survey_session
        return context


class TreatmentPlaceboThanks(TemplateView):

    template_name = 'facebook-experiment-placebo-thanks.html'


class TreatmentPolitics(TemplateView):

    template_name = 'facebook-experiment-politics.html'

    def get(self, request, *args, **kwargs):
        self.survey_session = request.GET.get('sid')

        return super(TreatmentPolitics, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TreatmentPolitics, self).get_context_data(**kwargs)
        context['form_counties'] = ConstituencyGroupedByCountySelectForm()
        context['sid'] = self.survey_session
        return context


class TreatmentPoliticsThanks(TemplateView):

    template_name = 'facebook-experiment-politics-thanks.html'
