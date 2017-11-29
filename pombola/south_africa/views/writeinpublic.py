from django.views.generic.edit import FormView
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponseServerError, Http404
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.decorators import method_decorator

from pombola.writeinpublic.forms import MessageForm
from pombola.core.models import Person
from pombola.writeinpublic.client import WriteInPublic


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
        self.client = WriteInPublic(settings.WRITEINPUBLIC_URL, settings.WRITEINPUBLIC_USERNAME, settings.WRITEINPUBLIC_API_KEY, settings.WRITEINPUBLIC_INSTANCE_ID)
        super(WriteInPublicMixin, self).__init__(*args, **kwargs)


class SAWriteToRepresentative(WriteInPublicMixin, FormView):
    template_name = "writeinpublic/person-write.html"
    form_class = MessageForm

    @method_decorator(person_everypolitician_uuid_required)
    def dispatch(self, *args, **kwargs):
        return super(SAWriteToRepresentative, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SAWriteToRepresentative, self).get_context_data(**kwargs)
        person_slug = self.kwargs['person_slug']
        person = get_object_or_404(Person, slug=person_slug)
        context['object'] = person
        return context

    def form_valid(self, form):
        person_slug = self.kwargs['person_slug']
        person = get_object_or_404(Person, slug=person_slug)
        response = self.client.create_message(
            author_name=form.cleaned_data['author_name'],
            author_email=form.cleaned_data['author_email'],
            subject=form.cleaned_data['subject'],
            content=form.cleaned_data['content'],
            writeitinstance="/api/v1/instance/{}/".format(self.client.instance_id),
            persons=["https://raw.githubusercontent.com/everypolitician/everypolitician-data/master/data/South_Africa/Assembly/ep-popolo-v1.0.json#person-{uuid}".format(uuid=person.everypolitician_uuid)],
        )
        if response.ok:
            message_id = response.json()['id']
            return HttpResponseRedirect(reverse('sa-writeinpublic-message', kwargs={'message_id': message_id}))
        else:
            # FIXME: This should do something more intelligent
            return HttpResponseServerError()


class SAWriteInPublicMessage(WriteInPublicMixin, TemplateView):
    template_name = 'writeinpublic/message.html'

    def get_context_data(self, **kwargs):
        context = super(SAWriteInPublicMessage, self).get_context_data(**kwargs)
        context['message'] = self.client.get_message(self.kwargs['message_id'])
        return context


class SAWriteToRepresentativeMessages(WriteInPublicMixin, TemplateView):
    template_name = 'writeinpublic/messages.html'

    @method_decorator(person_everypolitician_uuid_required)
    def dispatch(self, *args, **kwargs):
        return super(SAWriteToRepresentativeMessages, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SAWriteToRepresentativeMessages, self).get_context_data(**kwargs)
        person_slug = self.kwargs['person_slug']
        person = get_object_or_404(Person, slug=person_slug)
        context['person'] = person
        if person.everypolitician_uuid is None:
            context['messages'] = []
        else:
            context['messages'] = self.client.get_messages(person.everypolitician_uuid)
        return context
