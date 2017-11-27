from pombola.writeinpublic.forms import MessageForm
from django.views.generic.edit import FormView

from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404

from pombola.core.models import Person
from pombola.writeinpublic.client import WriteInPublic


class SAWriteToRepresentative(FormView):
    template_name = "writeinpublic/person-write.html"
    form_class = MessageForm
    # TODO: Change this to redirect to message page
    success_url = '/person/write/confirmation/'

    def get_context_data(self, **kwargs):
        context = super(SAWriteToRepresentative, self).get_context_data(**kwargs)
        person_slug = self.kwargs['person_slug']
        person = get_object_or_404(Person, slug=person_slug)
        context['object'] = person
        return context

    def form_valid(self, form):
        # FIXME: These values should come from config
        person_slug = self.kwargs['person_slug']
        person = get_object_or_404(Person, slug=person_slug)
        client = WriteInPublic("http://10.11.12.13.xip.io:8000", "admin", "123abc")
        r = client.create_message(
            author_name=form.cleaned_data['author_name'],
            author_email=form.cleaned_data['author_email'],
            subject=form.cleaned_data['subject'],
            content=form.cleaned_data['content'],
            # FIXME: This shouldn't be hard-coded
            writeitinstance="/api/v1/instance/3/",
            # FIXME: This shouldn't be hard-coded
            persons=["https://raw.githubusercontent.com/everypolitician/everypolitician-data/master/data/South_Africa/Assembly/ep-popolo-v1.0.json#person-{uuid}".format(uuid=person.everypolitician_uuid)],
        )
        return super(SAWriteToRepresentative, self).form_valid(form)


class SAWriteInPublicMessage(TemplateView):
    template_name = 'writeinpublic/message.html'

    def get_context_data(self, **kwargs):
        context = super(SAWriteInPublicMessage, self).get_context_data(**kwargs)
        client = WriteInPublic("http://10.11.12.13.xip.io:8000", "admin", "123abc")
        context['message'] = client.get_message(8)
        return context
