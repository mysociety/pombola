from django.http import JsonResponse
from django.views.generic import ListView

from pombola.core.models import Person, Organisation, Position


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


# Output Popolo JSON suitable for WriteInPublic for National Assembly members that have an
# email address.
class NAMembersPopoloJson(ListView):
    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(
            {
                "persons": [
                    {
                        "id": str(person.id),
                        "name": person.name,
                        "email": person.contacts.filter(kind__slug="email")
                        .order_by("-preferred")
                        .first()
                        .value.strip(),
                        "contact_details": [],
                        "memberships": [
                            {
                                "id": "membership-{}".format(person.id),
                                "person_id": str(person.id),
                                "role": "member",
                            },
                        ],
                    }
                    for person in context["object_list"]
                ]
            }
        )

    def get_queryset(self):
        positions = Position.objects.currently_active().filter(organisation__slug='national-assembly')
        person_ids = positions.values_list("person", flat=True).distinct()
        return Person.objects.filter(id__in=person_ids, contacts__kind__slug="email").distinct()
