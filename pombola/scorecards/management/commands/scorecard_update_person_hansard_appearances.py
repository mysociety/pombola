import datetime

from django.core.management.base import NoArgsCommand
from django.core.exceptions import ImproperlyConfigured

class Command(NoArgsCommand):
    help = 'Create/update hansard scorecard entry for all mps'
    args = ''

    def handle_noargs(self, **options):
        # Imports are here to avoid an import loop created when the Hansard
        # search indexes are checked
        from pombola.core.models import Person
        from pombola.scorecards.models import Category, Entry

        # create the category
        try:
            category = Category.objects.get(slug="hansard-appearances")
        except Category.DoesNotExist:
            raise ImproperlyConfigured("Please create a scorecard category with the slug 'hansard-appearances'")

        # Find all the people we should score for
        people = Person.objects.all().is_politician()
        
        # How far back should we look for hansard appearances?
        duration_string = "six months"
        lower_limit = datetime.date.today() - datetime.timedelta(183)

        for person in people:
            # NOTE: We could certainly do all this in a single query.
            hansard_count = person.hansard_entries.filter(sitting__start_date__gte=lower_limit).count()

            try:
                entry = person.scorecard_entries.get(category=category)
            except Entry.DoesNotExist:
                entry = Entry(content_object=person, category=category)

            if hansard_count < 6:
                entry.score = -1

                # deal with the various ways we need to phrase this
                if hansard_count == 0:
                    entry.remark = "Has not spoken in parliament in the last %s" % ( duration_string )
                elif hansard_count == 1:
                    entry.remark = "Only spoke once in parliament in the last %s" % ( duration_string )
                else:
                    entry.remark = "Hardly ever spoke in parliament, only %u times in the last %s" % ( hansard_count, duration_string )

            elif hansard_count < 60:
                entry.score = 0
                entry.remark = "Sometimes spoke in parliament, %u times in the last %s" % ( hansard_count, duration_string )
            else:
                entry.score = 1
                entry.remark = "Frequently spoke in parliament, %u times in the last %s" % ( hansard_count, duration_string )
            
            entry.date = datetime.date.today()

            entry.save()

        
        

