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
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        form.send_message()
        return super(SAWriteToRepresentative, self).form_valid(form)


class SAWriteInPublicMessage(TemplateView):
    template_name = 'writeinpublic/message.html'

    def get_context_data(self, **kwargs):
        context = super(SAWriteInPublicMessage, self).get_context_data(**kwargs)
        client = WriteInPublic("http://10.11.12.13.xip.io:8000", "admin", "123abc")
        context['message'] = client.get_message(8)
        return context
