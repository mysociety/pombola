from pombola.core.models import Place, Position

class ZAPlace(Place):
    class Meta:
        proxy = True

    def postal_addresses(self):
        return self.organisation.contacts.filter(kind__slug='address')

    def related_positions(self):
        return Position.objects.filter(organisation=self.organisation)
