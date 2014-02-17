"""Change party of everyone currently in ACN, ANPP and CPP to APC.

Update Positions of every current member of ACN, ANPP, and CPP to
have an end_date of 2013-07-30, and for each of them, make a new
Position with start_date 2013-07-31, no end date, and organisation
APC.

This is all very hard-coded, but might be useful as the bones of
a change party command later on.
"""
import datetime

from django.core.management.base import NoArgsCommand

from django_date_extensions.fields import ApproximateDate

from pombola.core.models import Position, Organisation

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        # acn, anpp, cpc
        old_party_slugs = (
            'action-congress-of-nigeria',
            'all-nigeria-peoples-party',
            'congress-for-progressive-change',
            )

        change_date = datetime.date(2013, 7, 31)
        old_party_end = ApproximateDate(2013, 7, 30)
        new_party_start = ApproximateDate(2013, 7, 31)

        new_party_slug = 'all-progressives-congress-apc'
        new_organisation = Organisation.objects.get(slug=new_party_slug)

        positions = (Position.objects.filter(
                         title__slug='member',
                         organisation__slug__in=old_party_slugs,
                         )
                     .currently_active(when=change_date)
                     )

        # Not using a bulk update because we want to the save
        # method of the Positions to be called
        for position in positions:
            position.end_date = old_party_end
            position.save()

            # Blank the primary key of the Position so that it will
            # get a new one when saved.
            position.pk = None
            position.start_date = new_party_start
            position.end_date = None
            position.organisation = new_organisation
            position.save()
