from formtools.wizard.views import NamedUrlSessionWizardView

from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from django.conf import settings
from django.utils.decorators import method_decorator
from django.contrib import messages

from pombola.core.models import Person

from .forms import RecipientForm, DraftForm, PreviewForm
from .client import WriteInPublic


def person_everypolitician_uuid_required(function):
    def wrap(request, *args, **kwargs):
        person = Person.objects.get(slug=kwargs['person_slug'])
        if person.everypolitician_uuid is None:
            raise Http404("Person is missing an EveryPolitician UUID")
        else:
            return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


class WriteInPublicMixin(object):
    def __init__(self, *args, **kwargs):
        self.client = WriteInPublic(
            settings.WRITEINPUBLIC_URL,
            settings.WRITEINPUBLIC_USERNAME,
            settings.WRITEINPUBLIC_API_KEY,
            settings.WRITEINPUBLIC_INSTANCE_ID
        )
        super(WriteInPublicMixin, self).__init__(*args, **kwargs)


FORMS = [
    ("recipients", RecipientForm),
    ("draft", DraftForm),
    ("preview", PreviewForm),
]

TEMPLATES = {
    'recipients': 'writeinpublic/person-write-recipients.html',
    'draft': 'writeinpublic/person-write-draft.html',
    'preview': 'writeinpublic/person-write-preview.html',
}


class WriteInPublicNewMessage(WriteInPublicMixin, NamedUrlSessionWizardView):
    form_list = FORMS

    def get(self, *args, **kwargs):
        step = kwargs.get('step')
        # If we have an ID in the URL and it matches someone, go straight to
        # /draft
        if 'person_id' in self.request.GET:
            person_id = self.request.GET['person_id']
            try:
                person = Person.objects.get(pk=person_id)
                self.storage.set_step_data('recipients', {'recipients-persons': [person.id]})
                self.storage.current_step = 'draft'
                return redirect(self.get_step_url('draft'))
            except Person.DoesNotExist:
                pass

        # Check that the form contains valid data
        if step == 'draft' or step == 'preview':
            recipients = self.get_cleaned_data_for_step('recipients')
            if recipients is None or recipients.get('persons') == []:
                # Form is missing persons, restart process
                self.storage.reset()
                self.storage.current_step = self.steps.first
                return redirect(self.get_step_url(self.steps.first))

        return super(WriteInPublicNewMessage, self).get(*args, **kwargs)

    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    def get_context_data(self, form, **kwargs):
        context = super(WriteInPublicNewMessage, self).get_context_data(form=form, **kwargs)
        context['message'] = self.get_cleaned_data_for_step('draft')
        recipients = self.get_cleaned_data_for_step('recipients')
        if recipients is not None:
            context['persons'] = recipients.get('persons')
        return context

    def done(self, form_list, form_dict, **kwargs):
        persons = form_dict['recipients'].cleaned_data['persons']
        person_ids = [p.everypolitician_uuid for p in persons]
        person_uris = ["https://raw.githubusercontent.com/everypolitician/everypolitician-data/master/data/South_Africa/Assembly/ep-popolo-v1.0.json#person-{}".format(uuid)
                       for uuid in person_ids]
        message = form_dict['draft'].cleaned_data
        try:
            response = self.client.create_message(
                author_name=message['author_name'],
                author_email=message['author_email'],
                subject=message['subject'],
                content=message['content'],
                persons=person_uris,
            )
            if response.ok:
                message_id = response.json()['id']
                messages.success(self.request, 'Success, your message has now been sent.')
                return redirect('writeinpublic-message', message_id=message_id)
            else:
                messages.error(self.request, 'Sorry, there was an error sending your message, please try again. If this problem persists please contact us.')
                return redirect('writeinpublic-new-message')
        except self.client.WriteInPublicException:
            messages.error(self.request, 'Sorry, there was an error connecting to the message service, please try again. If this problem persists please contact us.')
            return redirect('writeinpublic-new-message')


class WriteInPublicMessage(WriteInPublicMixin, TemplateView):
    template_name = 'writeinpublic/message.html'

    def get_context_data(self, **kwargs):
        context = super(WriteInPublicMessage, self).get_context_data(**kwargs)
        context['message'] = self.client.get_message(self.kwargs['message_id'])
        return context


class WriteToRepresentativeMessages(WriteInPublicMixin, TemplateView):
    template_name = 'writeinpublic/messages.html'

    @method_decorator(person_everypolitician_uuid_required)
    def dispatch(self, *args, **kwargs):
        return super(WriteToRepresentativeMessages, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(WriteToRepresentativeMessages, self).get_context_data(**kwargs)
        person_slug = self.kwargs['person_slug']
        person = get_object_or_404(Person, slug=person_slug)
        context['person'] = person
        if person.everypolitician_uuid is None:
            context['messages'] = []
        else:
            person_uri = 'https://raw.githubusercontent.com/everypolitician/everypolitician-data/master/data/South_Africa/Assembly/ep-popolo-v1.0.json#person-{}'.format(person.everypolitician_uuid)
            context['messages'] = self.client.get_messages(person_uri)
        return context
