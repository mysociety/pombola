from django.views.generic import ListView

from pombola.core.models import Organisation, OrganisationKind


class SACommitteesView(ListView):
    queryset = Organisation.objects.filter(
        kind__name='National Assembly Committees',
        contacts__kind__slug='email'
    ).distinct().order_by('short_name')
    context_object_name = 'committees'
    template_name = 'south_africa/committee_list.html'

    def get_context_data(self, *args, **kwargs):
        context = super(SACommitteesView, self).get_context_data(*args, **kwargs)
        context['kind'] = OrganisationKind.objects.get(name='National Assembly Committees')
        return context
