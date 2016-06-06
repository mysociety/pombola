import datetime

from django import forms
from django.forms.widgets import Textarea

from pombola.core.models import Place

from .election_data_2017.iebc_offices import IEBC_OFFICE_DATA


class CountyPerformancePetitionForm(forms.Form):
    name = forms.CharField(
        error_messages={'required': 'You must enter a name'},
        widget=forms.TextInput(
            attrs={
                'required': 'required',
                'placeholder': 'Your name'}))
    email = forms.EmailField(
        error_messages={'required': 'You must enter a valid email address'},
        widget=forms.TextInput(
            attrs={
                'required': 'required',
                'placeholder': 'Your email address'}))

    def clean(self):
        # We want to provide a single helpful error message if both
        # name and email address aren't supplied, so override clean to
        # detect that condition
        cleaned_data = super(CountyPerformancePetitionForm,
                             self).clean()
        if not cleaned_data:
            raise forms.ValidationError(
                "You must specify a name and a valid email address")
        return cleaned_data


class CountyPerformanceSenateForm(forms.Form):
    comments = forms.CharField(
        label='Tell the senate what would like to see in your county',
        error_messages={'required': "You didn't enter a comment"},
        widget=Textarea(
            attrs={
                'rows': 5,
                'cols': 60,
                'required': 'required',
                'placeholder': 'Add any comments here'}))


class YouthEmploymentCommentForm(forms.Form):
    comments = forms.CharField(
        label='Give us your comments on the Bill',
        error_messages={'required': "You didn't enter a comment"},
        widget=Textarea(
            attrs={
                'rows': 5,
                'cols': 60,
                'required': 'required',
                'placeholder': 'Add any comments here'}))


class NamedModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name

class YouthEmploymentSupportForm(forms.Form):

    constituencies = NamedModelChoiceField(
        queryset = Place.objects.filter(
                    kind__slug='constituency',
                    parliamentary_session__end_date__gte=datetime.date.today()
                   ).order_by('name'),
        empty_label = "Choose your constituency",
        error_messages={'required': "Please choose a constituency"}
    )

class YouthEmploymentInputForm(forms.Form):
    pass


_offices_by_county = {}
for _o in IEBC_OFFICE_DATA:
    c_name = _o['coun_name']
    _offices_by_county.setdefault(c_name, [])
    _offices_by_county[c_name].append((_o['cons_id'], _o['cons_name']))

OFFICES_BY_COUNTY_CHOICES = sorted(_offices_by_county.items())
for _county_name, _offices in OFFICES_BY_COUNTY_CHOICES:
    _offices.sort(key=lambda t: t[1])
OFFICES_BY_COUNTY_CHOICES.insert(0, ('', ''))


class ConstituencyGroupedByCountySelectForm(forms.Form):
    area = forms.ChoiceField(choices=OFFICES_BY_COUNTY_CHOICES)
