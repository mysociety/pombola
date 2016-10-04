from __future__ import print_function

from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand
from django.db import transaction

from instances.models import Instance
from popolo import models as popolo_models
from pombola.core import models as pombola_models
from pombola_sayit.models import PombolaSayItJoin
from slug_helpers.models import SlugRedirect
from speeches.models import Speaker


def convert_approximate_date(approx_date):
    if approx_date is None:
        return None
    if approx_date.future or approx_date.past:
        return None
    return repr(approx_date)


class Command(BaseCommand):

    def update_person_from_pombola(self, pombola_person, speaker):
        if self.verbose:
            print("Updating the Pombola person:", pombola_person.name)
        # Update the the name information in flat fields:
        for person_attr, speaker_attr in (
                ('legal_name', 'name'),
                ('family_name', 'family_name'),
                ('given_name', 'given_name'),
                ('honorific_prefix', 'honorific_prefix'),
                ('honorific_suffix', 'honorific_suffix'),
                ('sort_name', 'sort_name'),
        ):
            setattr(
                speaker,
                speaker_attr,
                getattr(pombola_person, person_attr)
            )
        # Also, there may be an existing image URL for the
        # Speaker. The Speaker model, however, will try to download
        # that image to create a thumbnail on save() which makes this
        # sync process very slow and reliant on a reliable network
        # connection and use lots of network data.  We already have
        # the photos associated with the Person in Pombola, and the
        # SayIt templates we use use the Pombola image instead of the
        # SayIt Speaker thumbnails, so remove anything in the image
        # field:
        speaker.image = None
        speaker.save()
        # Now create the alternative names:
        for alt_name in pombola_person.alternative_names.all():
            popolo_models.OtherName.objects.create(
                name=alt_name.alternative_name,
                content_object=speaker,
                start_date=convert_approximate_date(alt_name.start_date),
                end_date=convert_approximate_date(alt_name.end_date),
            )
        # Make sure that the slugs that are associated with people are
        # stored as identifiers so that we can use them to help in
        # name resolution. (We have Pombola URLs from the Code4SA
        # question and answer data.)
        all_slugs = set([pombola_person.slug])
        all_slugs.update(self.person_to_slug_redirects[pombola_person])
        for slug in all_slugs:
            speaker.identifiers.create(
                scheme='pombola_person_slug',
                identifier=slug)
        # And go through every position and create corresponding memberships:
        for position in pombola_person.position_set.all():
            # Make sure the organisation exists:
            popolo_org = None
            pombola_org = position.organisation
            if not pombola_org:
                # Memberships without organizations aren't useful for
                # name resolution, and are only supported in Popolo if
                # the membership refers to a Post instead. (We don't
                # have anything quite like Popolo's Post in Pombola;
                # PositionTitle is a slightly different concept.)
                continue
            if self.verbose:
                print("  Adding position in organisation", pombola_org)
            if pombola_org in self.org_cache:
                popolo_org = self.org_cache[pombola_org]
            else:
                popolo_org = popolo_models.Organization.objects.create(
                    name=pombola_org.name[:128],
                    classification=pombola_org.kind.name
                )
                self.org_cache[pombola_org] = popolo_org
            # And then create the membership based on the position:
            popolo_models.Membership.objects.create(
                organization=popolo_org,
                person=speaker,
                start_date=convert_approximate_date(position.start_date),
                end_date=convert_approximate_date(position.end_date),
            )

    def cache_slug_redirects(self):
        self.person_to_slug_redirects = defaultdict(set)
        ct = ContentType.objects.get(app_label='core', model='person')
        for sr in SlugRedirect.objects.filter(content_type=ct):
            self.person_to_slug_redirects[sr.new_object].add(
                sr.old_object_slug)

    def handle(self, *args, **options):
        self.verbose = int(options['verbosity']) > 1
        self.cache_slug_redirects()
        instance = Instance.objects.get()
        self.org_cache = {}
        # Delete all data from Popolo models that are associated
        # with people and we care about the name resolver having
        # data for, because we'll recreate them in this command.
        for model in (
                popolo_models.Membership,
                popolo_models.Organization,
                popolo_models.OtherName,
        ):
            model.objects.all().delete()
        popolo_models.Identifier.objects.filter(scheme='pombola_person_slug') \
            .delete()
        for pombola_person in pombola_models.Person.objects.all():
            with transaction.atomic():
                try:
                    speaker = pombola_person.sayit_link.sayit_speaker
                except PombolaSayItJoin.DoesNotExist:
                    speaker = Speaker.objects.create(
                        instance=instance,
                        name=pombola_person.legal_name,
                    )
                    PombolaSayItJoin.objects.create(
                        pombola_person=pombola_person,
                        sayit_speaker=speaker,
                    )
                self.update_person_from_pombola(pombola_person, speaker)
