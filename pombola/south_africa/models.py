from pombola.core.models import Place, PopoloMembership, PopoloOrganization


class ZAPlace(Place):
    class Meta:
        proxy = True

    def postal_addresses(self):
        return self.organisation.contacts.filter(kind__slug='address')

    def related_positions(self):
        return Position.objects.filter(organisation=self.organisation)

    def party(self):
        """Find the party associated with a place.

        If a place is the one associated with a constituency office or area,
        then find the party associated with it.
        """
        # FIXME - share this list with views
        if self.organisation.kind.slug in ('constituency-office', 'constituency-area'):
            return Organisation.objects.get(
                org_rels_as_a__kind__name='has_office',
                org_rels_as_a__organisation_b=self.organisation,
                kind__slug='party',
                )
            
