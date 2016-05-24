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

SURVEYGIZMO_SURVEY_URL = "https://restapi.surveygizmo.com/v4/survey/2802241/"
SURVEYGIZMO_SID_QUESTION_ID = "13"

SURVEYGIZMO_OLYMPICS_1_QUESTION_ID = "62"
SURVEYGIZMO_OLYMPICS_1_ANSWER_ID = "10173"

SURVEYGIZMO_OLYMPICS_2_QUESTION_ID = "58"
SURVEYGIZMO_OLYMPICS_2_ANSWER_ID = "10170"

SURVEYGIZMO_POLITICS_1_QUESTION_ID = "61"
SURVEYGIZMO_POLITICS_1_ANSWER_ID = "10172"

SURVEYGIZMO_POLITICS_2_QUESTION_ID = "59"
SURVEYGIZMO_POLITICS_2_ANSWER_ID = "10171"


class TreatmentOlympics(TemplateView):

    template_name = 'facebook-experiment-olympics.html'

    def get(self, request, *args, **kwargs):
        self.survey_session = request.GET.get('sid')

        if self.survey_session:
            _record_positive_response(self.survey_session,
                                      SURVEYGIZMO_OLYMPICS_1_QUESTION_ID,
                                      SURVEYGIZMO_OLYMPICS_1_ANSWER_ID
                                      )

        return super(TreatmentOlympics, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TreatmentOlympics, self).get_context_data(**kwargs)
        context['sid'] = self.survey_session
        return context


class TreatmentOlympicsThanks(TemplateView):

    template_name = 'facebook-experiment-olympics-thanks.html'

    def get(self, request, *args, **kwargs):
        survey_session = request.GET.get('sid')

        if survey_session:
            _record_positive_response(survey_session,
                                      SURVEYGIZMO_OLYMPICS_2_QUESTION_ID,
                                      SURVEYGIZMO_OLYMPICS_2_ANSWER_ID
                                      )

        return super(TreatmentOlympicsThanks, self).get(request, *args, **kwargs)


class TreatmentPolitics(TemplateView):

    template_name = 'facebook-experiment-politics.html'

    def get(self, request, *args, **kwargs):
        self.survey_session = request.GET.get('sid')

        if self.survey_session:
            _record_positive_response(self.survey_session,
                                      SURVEYGIZMO_POLITICS_1_QUESTION_ID,
                                      SURVEYGIZMO_POLITICS_1_ANSWER_ID
                                      )

        return super(TreatmentPolitics, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TreatmentPolitics, self).get_context_data(**kwargs)
        context['form_counties'] = ConstituencyGroupedByCountySelectForm()
        context['sid'] = self.survey_session
        return context


class TreatmentPoliticsThanks(TemplateView):

    template_name = 'facebook-experiment-politics-thanks.html'

    def get(self, request, *args, **kwargs):
        survey_session = request.GET.get('sid')

        if survey_session:
            _record_positive_response(survey_session,
                                      SURVEYGIZMO_POLITICS_2_QUESTION_ID,
                                      SURVEYGIZMO_POLITICS_2_ANSWER_ID
                                      )

        return super(TreatmentPoliticsThanks, self).get(request, *args, **kwargs)


class SurveyGizmoRecord(TemplateView):

    # The survey doesn't actually care if this works or not, just send an "OK".
    template_name = 'facebook-ajax-response.html'

    def get(self, request, *args, **kwargs):
        survey_session = request.GET.get('sid')
        question_id = request.GET.get('qid')
        selection_id = request.GET.get('selid')

        if survey_session and question_id and selection_id:
            _record_positive_response(survey_session, question_id, selection_id)

        return super(SurveyGizmoRecord, self).get(request, *args, **kwargs)


class SurveyGizmoValue(TemplateView):

    # The survey doesn't actually care if this works or not, just send an "OK".
    template_name = 'facebook-ajax-response.html'

    def get(self, request, *args, **kwargs):
        survey_session = request.GET.get('sid')
        question_id = request.GET.get('qid')
        value = request.GET.get('value')

        if survey_session and question_id and value:
            _record_response_value(survey_session, question_id, value)

        return super(SurveyGizmoValue, self).get(request, *args, **kwargs)


def _get_survey_id_from_session(survey_session):

    survey_id = cache.get(survey_session)

    if not survey_id:

        url = SURVEYGIZMO_SURVEY_URL + "surveyresponse/"

        querystring = {
            "api_token": settings.SURVEYGIZMO_API_TOKEN,
            "api_token_secret": settings.SURVEYGIZMO_API_SECRET,
            "filter[field][0]": "[question(" + SURVEYGIZMO_SID_QUESTION_ID + ")]",
            "filter[operator][0]": "=",
            "filter[value][0]": survey_session
        }

        headers = {
            'cache-control': "no-cache"
        }

        response = requests.get(url,
                                headers=headers,
                                params=querystring
                                )
        data = response.json()

        # Sanity check we have a response, and only one. If not, abandon ship.
        if 'total_count' in data and int(data['total_count']) == 1:
            survey = data['data'][0]
            survey_id = survey['id']

        else:
            survey_id = None

        cache.set(survey_session, survey_id, 1800)

        return survey_id


def _record_positive_response(survey_session, question_id, selection_id):

    # Get the survey ID
    survey_id = _get_survey_id_from_session(survey_session)

    # Sanity check that it's a real survey ID
    if survey_id:

        url = SURVEYGIZMO_SURVEY_URL + "surveyresponse/" + survey_id + "/"

        querystring = {
            "api_token": settings.SURVEYGIZMO_API_TOKEN,
            "api_token_secret": settings.SURVEYGIZMO_API_SECRET,
            "data[" + question_id + "][" + selection_id + "]": "Yes"
        }

        headers = {
            'cache-control': "no-cache",
        }

        response = requests.post(url, headers=headers, params=querystring)

        # Throw an exception if something bad happened.
        response.raise_for_status()


def _record_response_value(survey_session, question_id, value):

    # Get the survey ID
    survey_id = _get_survey_id_from_session(survey_session)

    # Sanity check that it's a real survey ID
    if survey_id:

        url = SURVEYGIZMO_SURVEY_URL + "surveyresponse/" + survey_id + "/"

        querystring = {
            "api_token": settings.SURVEYGIZMO_API_TOKEN,
            "api_token_secret": settings.SURVEYGIZMO_API_SECRET,
            "data[" + question_id + "][value]": value
        }

        headers = {
            'cache-control': "no-cache",
        }

        response = requests.post(url, headers=headers, params=querystring)

        # Throw an exception if something bad happened.
        response.raise_for_status()
