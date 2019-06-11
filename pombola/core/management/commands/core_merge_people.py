# This admin command is to save having to do a series of manual steps
# when merging to people in Pombola.

from django.conf import settings

import pombola.core.models as core_models
from pombola.core.views import PersonSpeakerMappingsMixin

from ..merge import MergeCommandBase


class Command(PersonSpeakerMappingsMixin, MergeCommandBase):
    admin_url_name = 'admin:core_person_change'
    basic_fields_to_check = (
        'date_of_birth',
        'date_of_death',
        'gender',
        'summary',
        'title',
        'hidden',
    )
    model_class = core_models.Person

    def model_specific_merge(self, to_keep, to_delete, **options):
        # Find names that might be lost and add it them as
        # alternative names to the person to keep:
        names_to_add = to_delete.all_names_set() - to_keep.all_names_set()

        for name in names_to_add:
            to_keep.add_alternative_name(name)

        # If a SayIt ID scheme is specified, move speeches from deleted person
        if 'speeches' in settings.INSTALLED_APPS:

            if not options['quiet']:
                print "Moving SayIt speeches"

            from speeches.models import Speech

            delete_sayit_speaker = self.pombola_person_to_sayit_speaker(
                to_delete)

            keep_sayit_speaker = self.pombola_person_to_sayit_speaker(
                to_keep)

            if delete_sayit_speaker and keep_sayit_speaker:
                Speech.objects.filter(
                    speaker=delete_sayit_speaker
                ).update(
                    speaker=keep_sayit_speaker
                )
            else:
                if not options['quiet']:
                    print "One or both of the people does not have a SayIt " \
                        "speaker. Not moving speeches."

        core_models.Position.objects.filter(person=to_delete).update(person=to_keep)

        # Then those in hansard, if that application is installed:
        #    hansard_models.Alias
        #    hansard_models.Entry
        if 'pombola.hansard' in settings.INSTALLED_APPS:
            import pombola.hansard.models as hansard_models

            if not options['quiet']:
                print "Moving Hansard entries"

            hansard_models.Alias.objects.filter(person=to_delete).update(person=to_keep)

            hansard_models.Entry.objects.filter(speaker=to_delete).update(speaker=to_keep)

        # (The scorecard application can be ignored, since those
        # results are regenerated automatically.)

        # Then those in interests_register, if that application is installed:
        #    interests_register_models.Entry
        if 'pombola.interests_register' in settings.INSTALLED_APPS:
            import pombola.interests_register.models as interests_register_models

            if not options['quiet']:
                print "Moving interests register entries"

            interests_register_models.Entry.objects.filter(person=to_delete).update(person=to_keep)
