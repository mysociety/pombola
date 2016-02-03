from ajax_select import LookupChannel

from .models import Person


class PersonLookup(LookupChannel):

    model = Person

    def get_query(self, q, requests):
        return Person.objects.filter(hidden=False, legal_name__icontains=q)
