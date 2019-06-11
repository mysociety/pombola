# This base class is to make it easier to write management commands
# for merging object in Pombola (e.g. Person and Organisation at the
# moment).

from optparse import make_option
import sys

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.core.urlresolvers import reverse
from django.db import transaction

from slug_helpers.models import SlugRedirect
from images.models import Image

import pombola.core.models as core_models


def check_basic_fields(basic_fields, to_keep, to_delete):
    """Return False if any data might be lost on merging"""

    safe_to_delete = True
    for basic_field in basic_fields:
        if basic_field == 'summary':
            # We can't just check equality of summary fields because
            # they are MarkupField fields which don't have equality
            # helpfully defined (and they're always different objects
            # between two different speakers), so instead, check for
            # equality of the rendered content of the summary.

            delete_value = to_delete.summary.rendered
            keep_value = to_keep.summary.rendered
        else:
            delete_value = getattr(to_delete, basic_field)
            keep_value = getattr(to_keep, basic_field)

        if keep_value != delete_value:
            # i.e. there's some data that might be lost:
            safe_to_delete = False
            message = "Mismatch in '%s': '%s' ({%d}) and '%s' (%d)"
            print >> sys.stderr, message % (basic_field,
                                            keep_value,
                                            to_keep.id,
                                            delete_value,
                                            to_delete.id)
    return safe_to_delete


class MergeCommandBase(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("--keep-object", dest="keep_object", type="string",
                    help="The ID or slug of the object to retain",
                    metavar="OBJECT-ID"),
        make_option("--delete-object", dest="delete_object", type="string",
                    help="The ID or slug of the object to delete",
                    metavar="OBJECT-ID"),
        make_option('--noinput',  dest='interactive',
                    action='store_false', default=True,
                    help="Do NOT prompt the user for input of any kind"),
        make_option("--quiet", dest="quiet",
                    help="Suppress progress output",
                    default=False, action='store_true'))

    admin_url_name = None
    basic_fields_to_check = ()
    model_class = None

    def model_specific_merge(self, to_keep, to_delete, **options):
        pass

    def get_by_slug_or_id(self, identifier):
        try:
            return self.model_class.objects.get(slug=identifier)
        # AttributeError catches the case where there is no slug field.
        except self.model_class.DoesNotExist, AttributeError:
            try:
                object_id = int(identifier)
            except ValueError:
                raise (
                    self.model_class.DoesNotExist,
                    "Object matching query does not exist."
                    )
            return self.model_class.objects.get(pk=object_id)

    @transaction.atomic
    def handle(self, *args, **options):
        if not options['keep_object']:
            raise CommandError("You must specify --keep-object")
        if not options['delete_object']:
            raise CommandError("You must specify --delete-object")
        if args:
            message = "Don't supply arguments, only --keep-object and --delete-object"
            raise CommandError(message)

        to_keep = self.get_by_slug_or_id(options['keep_object'])
        to_delete = self.get_by_slug_or_id(options['delete_object'])

        to_keep_admin_url = reverse(self.admin_url_name, args=(to_keep.id,))

        if to_keep.id == to_delete.id:
            raise CommandError("--keep-object and --delete-object are the same")

        print "Going to keep:", to_keep, "with ID", to_keep.id
        print "Going to delete:", to_delete, "with ID", to_delete.id

        if options['interactive']:
            answer = raw_input('Do you wish to continue? (y/[n]): ')
            if answer != 'y':
                raise CommandError("Command halted by user, no changes made")

        if not check_basic_fields(
            self.basic_fields_to_check,
            to_keep,
            to_delete,
        ):
            raise CommandError("You must resolve differences in the above fields")

        content_type = ContentType.objects.get_for_model(self.model_class)

        self.model_specific_merge(to_keep, to_delete, **options)

        # Replace the object on all models with generic foreign keys in core

        for model in (core_models.Contact,
                      core_models.Identifier,
                      core_models.InformationSource):
            model.objects.filter(content_type=content_type,
                                 object_id=to_delete.id) \
                .update(object_id=to_keep.id)

        # Add any images for the object to delete as non-primary
        # images for the object to keep:
        Image.objects.filter(content_type=content_type,
                             object_id=to_delete.id) \
                .update(is_primary=False,
                        object_id=to_keep.id)
        # Make sure the old slug redirects to the object to keep:
        SlugRedirect.objects.create(
            new_object=to_keep,
            old_object_slug=to_delete.slug,
            )
        # Finally delete the now unnecessary object:
        to_delete.delete()

        if not options['quiet']:
            print "Now check the remaining object (", to_keep_admin_url, ")"
            print "for any duplicate information."
