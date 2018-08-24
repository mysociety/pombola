from django.http import JsonResponse
from django.views.generic import ListView

from pombola.core.models import Organisation


# Output Popolo JSON suitable for WriteInPublic for any committees that have an
# email address.
class CommitteesPopoloJson(ListView):
    queryset = Organisation.objects.filter(
        kind__name='National Assembly Committees',
        contacts__kind__slug='email'
    )

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(
            {
                'persons': [
                    {
                        'id': str(committee.id),
                        'name': committee.short_name,
                        'email': committee.contacts.filter(kind__slug='email')[0].value,
                        'contact_details': []
                    }
                    for committee in context['object_list']
                ]
            }
        )
