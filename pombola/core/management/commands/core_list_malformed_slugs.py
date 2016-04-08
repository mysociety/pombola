import re
from optparse import make_option

from slug_helpers.models import SlugRedirect

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify

working_slug_re = re.compile(r'^[-\w]+$')

class Command(BaseCommand):
    help = 'List slugs that are not correctly formed'

    option_list = BaseCommand.option_list + (
        make_option('--correct', action='store_true', dest='correct', help='Correct bad slugs'),
    )

    def handle(self, **options):
        """For each model check all the slugs are as expected"""

        models_to_check = self.get_list_of_models_to_check()
        bad_slug_count = 0

        for model, redirectable in models_to_check:
            for row in model.objects.only('id', 'slug').all():
                raw_slug = row.slug
                create_redirect = working_slug_re.search(raw_slug) and redirectable
                correct_slug = slugify(raw_slug)
                if raw_slug != correct_slug:
                    bad_slug_count += 1
                    kwargs = dict(model=model, raw=raw_slug, correct=correct_slug, id=row.id)
                    existing = model.objects.filter(slug=correct_slug)
                    if existing:
                        msg = u"Couldn't correct slug {bad_slug} to "
                        msg += u"{good_slug}, because a {model} with slug "
                        msg += u"{good_slug} already exists, with ID "
                        msg += u"{object_id}"
                        raise CommandError(msg.format(
                            bad_slug=raw_slug,
                            good_slug=correct_slug,
                            model=model,
                            object_id=existing[0].id
                        ))
                    if options['correct']:
                        template = u"Corrected {model} (id {id}): '{raw}' is now '{correct}'"
                        row.slug = correct_slug
                        row.save()
                        # If the old slug actually would have worked,
                        # and we support redirections for this model,
                        # then create a SlugRedirect:
                        if create_redirect:
                            SlugRedirect.objects.create(
                                content_type=ContentType.objects.get_for_model(model),
                                old_object_slug=raw_slug,
                                new_object_id=row.id,
                                new_object=row,
                            )
                    else:
                        template = u"Bad slug in {model} (id {id}): '{raw}' should be '{correct}'"
                        if create_redirect:
                            template += "\n  (would create a redirect)"

                    print template.format(**kwargs)

        if bad_slug_count and not options['correct']:
            print
            print "You can auto correct these slugs with the '--correct' flag"

    def get_list_of_models_to_check(self):
        """
        Return a list of tuples of slugged models and if they're redirectable

        Perhaps would be better to find models using some form of introspection,
        but for now a good way to find all the slug fields is to search for
        'models.SlugField'.
        """

        # Models that will always be available
        from pombola import core, info, tasks
        models_to_check = (
            (core.models.ContactKind, False),
            (core.models.Person, True),
            (core.models.OrganisationKind, False),
            (core.models.Organisation, True),
            (core.models.PlaceKind, False),
            (core.models.Place, True),
            (core.models.PositionTitle, False),
            (core.models.ParliamentarySession, False),
            (info.models.InfoPage, False),
            (tasks.models.TaskCategory, False),
        )

        OPTIONAL_APPS = settings.OPTIONAL_APPS

        if 'hansard' in OPTIONAL_APPS:
            from pombola import hansard
            models_to_check.append((hansard.models.Venue, False))

        if 'scorecards' in OPTIONAL_APPS:
            from pombola import scorecards
            models_to_check.append((scorecards.models.Category, False))

        if 'votematch' in OPTIONAL_APPS:
            from pombola import votematch
            models_to_check.append((votematch.models.Quiz, False))

        return models_to_check
