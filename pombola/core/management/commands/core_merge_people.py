# This admin command is to save having to do a series of manual steps
# when merging to people in Pombola.

import sys

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.core.urlresolvers import reverse
from django.db import transaction

import pombola.core.models as core_models
from pombola.images.models import Image

from django.conf import settings

from optparse import make_option


def check_basic_fields(basic_fields, to_keep, to_delete):
    """Return False if any data might be lost on merging"""

    safe_to_delete = True
    for basic_field in basic_fields:
        delete_value = getattr(to_delete, basic_field)
        keep_value = getattr(to_keep, basic_field)
        if delete_value and (keep_value != delete_value):
            # i.e. there's some data that might be lost:
            safe_to_delete = False
            message = "Mismatch in '%s': '%s' ({%d}) and '%s' (%d)"
            print >> sys.stderr, message % (basic_field,
                                            keep_value,
                                            to_keep.id,
                                            delete_value,
                                            to_delete.id)
    return safe_to_delete


class Command(BaseCommand):

    help = "Merge two Person records into one, deleting one of the originals"
    option_list = BaseCommand.option_list + (
        make_option("--keep-person", dest="keep_person", type="int",
                    help="The ID of the person to retain",
                    metavar="PERSON-ID"),
        make_option("--delete-person", dest="delete_person", type="int",
                    help="The ID of the person to delete",
                    metavar="PERSON-ID"),
        make_option("--quiet", dest="quiet",
                    help="Suppress progress output",
                    default=False, action='store_true'))

    @transaction.commit_on_success
    def handle(self, *args, **options):
        if not options['keep_person']:
            raise CommandError("You must specify --keep-person")
        if not options['delete_person']:
            raise CommandError("You must specify --delete-person")
        if args:
            message = "Don't supply arguments, only --keep-person and --delete-person"
            raise CommandError(message)

        verbose = int(options['verbosity']) > 1

        to_keep = core_models.Person.objects.get(pk=options['keep_person'])
        to_delete = core_models.Person.objects.get(pk=options['delete_person'])

        to_keep_admin_url = reverse('admin:core_person_change',
                                    args=(to_keep.id,))

        if not options['quiet']:
            print "Going to keep:", to_keep, "with ID", to_keep.id
            print "Going to delete:", to_delete, "with ID", to_delete.id

        if not check_basic_fields(['title',
                                   'gender',
                                   'date_of_birth',
                                   'date_of_death',
                                   'summary'],
                                  to_keep,
                                  to_delete):
            raise CommandError("You must resolve differences in the above fields")

        content_type_person = ContentType.objects.get(model="person",
                                                      app_label="core")

        # Find names that might be lost and add it them as
        # alternative names to the person to keep:
        names_to_add = to_delete.all_names_set() - to_keep.all_names_set()
        for name in names_to_add:
            to_keep.add_alternative_name(name)
        # Switch the person or speaker model on all affected
        # models in core:
        #    core_models.Position
        #    core_models.Contact
        #    core_models.Identifier
        #    core_models.InformationSource
        core_models.Position.objects.filter(person=to_delete).update(person=to_keep)
        for model in (core_models.Contact,
                      core_models.Identifier,
                      core_models.InformationSource):
            model.objects.filter(content_type=content_type_person,
                                 object_id=to_delete.id) \
                .update(object_id=to_keep.id)
        # Then those in hansard, if that application is installed:
        #    hansard_models.Alias
        #    hansard_models.Entry
        if 'hansard' in settings.INSTALLED_APPS:
            import pombola.hansard.models as hansard_models
            hansard_models.Alias.objects.filter(person=to_delete).update(person=to_keep)
            hansard_models.Entry.objects.filter(speaker=to_delete).update(speaker=to_keep)
        # (The scorecard application can be ignored, since those
        # results are regenerated automatically.)

        # Add any images for the person to delete as non-primary
        # images for the person to keep:
        Image.objects.filter(content_type=content_type_person,
                             object_id=to_delete.id) \
                .update(is_primary=False,
                        object_id=to_keep.id)
        # Make sure the old slug redirects to the person to keep:
        core_models.SlugRedirect.objects.create(new_object=to_keep,
                                                old_object_slug=to_delete.slug)
        # Finally delete the now unnecessary person:
        to_delete.delete()

        if not options['quiet']:
            print "Now check the remaining profile (", to_keep_admin_url, ")"
            print "for any duplicate information."
