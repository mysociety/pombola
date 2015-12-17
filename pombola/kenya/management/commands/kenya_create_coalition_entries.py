from django.core.management.base import BaseCommand
from pombola.core import models


class Command(BaseCommand):
    """
    Create the entries needed for the coalitions. This is a one off script and
    is just here to make creating the entries easier during development and to
    ensure that the slugs are the same as the values hard coded into other
    scripts.
    """

    help = 'Create coalition related entries'

    def handle(self, **options):

        print "Creating coalition org kind"
        coalition_kind, created = models.OrganisationKind.objects.get_or_create(
            slug = "coalition",
            name = "Coalition",
        );

        print "Creating the coalitions"
        coalitions = [
            # ( slug, name )
            ( 'amani',   'Amani (Peace) Coalition'           ),
            ( 'cord',    'Coalition for Reforms & Democracy' ),
            ( 'jubilee', 'Jubilee Alliance'                  ),
            ( 'eagle',   'The Eagle Coalition'               ),
        ]
        for slug, name in coalitions:
            models.Organisation.objects.get_or_create(
                slug = slug,
                name = name,
                kind = coalition_kind
            );
            
