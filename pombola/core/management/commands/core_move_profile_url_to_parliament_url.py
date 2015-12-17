from django.core.management.base import BaseCommand

from pombola.core.models import Contact, ContactKind


class Command(BaseCommand):
    help = 'Deduplicate the position entries'

    def handle(self, **options):
        """Change the kind of each Profile URL contact to a Parliament URL"""

        profile_url_kind, created = ContactKind.objects.get_or_create(slug='profile_url', name="Profile URL")
        parliament_url_kind, created = ContactKind.objects.get_or_create(slug='parliament_url', name="Parliament URL")

        for contact in Contact.objects.filter(kind=profile_url_kind):
            contact.kind = parliament_url_kind
            contact.save()
