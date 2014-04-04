from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'List slugs that are not correctly formed'

    option_list = BaseCommand.option_list + (
        make_option('--correct', action='store_true', dest='correct', help='Correct bad slugs'),
    )

    def handle(self, **options):
        """For each model check all the slugs are as expected"""

        models_to_check = self.get_list_of_models_to_check()
        bad_slug_count = 0

        for model in models_to_check:
            for row in model.objects.only('id', 'slug').all():
                raw_slug = row.slug
                correct_slug = slugify(raw_slug)
                if raw_slug != correct_slug:
                    bad_slug_count += 1
                    kwargs = dict(model=model, raw=raw_slug, correct=correct_slug, id=row.id)

                    if options['correct']:
                        template = u"Corrected {model} (id {id}): '{raw}' is now '{correct}'"
                        row.slug = correct_slug
                        row.save()
                    else:
                        template = u"Bad slug in {model} (id {id}): '{raw}' should be '{correct}'"

                    print template.format(**kwargs)

        if bad_slug_count and not options['correct']:
            print
            print "You can auto correct these slugs with the '--correct' flag"

    def get_list_of_models_to_check(self):
        """
        Return array containing all models that have a slug field.

        Perhaps would be better to find models using some form of introspection,
        but for now a good way to find all the slug fields is to search for
        'models.SlugField'.
        """

        # Models that will always be available
        from pombola import core, file_archive, info, tasks
        models_to_check = (
            core.models.ContactKind,
            core.models.Person,
            core.models.OrganisationKind,
            core.models.Organisation,
            core.models.PlaceKind,
            core.models.Place,
            core.models.PositionTitle,
            core.models.ParliamentarySession,
            file_archive.models.File,
            info.models.InfoPage,
            tasks.models.TaskCategory,
        )

        OPTIONAL_APPS = settings.OPTIONAL_APPS

        if 'hansard' in OPTIONAL_APPS:
            from pombola import hansard
            models_to_check.append(hansard.models.Venue)

        if 'scorecards' in OPTIONAL_APPS:
            from pombola import scorecards
            models_to_check.append(scorecards.models.Category)

        if 'votematch' in OPTIONAL_APPS:
            from pombola import votematch
            models_to_check.append(votematch.models.Quiz)

        return models_to_check
