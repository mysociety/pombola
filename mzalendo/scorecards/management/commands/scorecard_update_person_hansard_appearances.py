import datetime

from django.core.management.base import NoArgsCommand
from django.core.exceptions import ImproperlyConfigured

class Command(NoArgsCommand):
    help = 'Create/update hansard scorecard entry for all mps'
    args = ''

    def handle_noargs(self, **options):
        # Imports are here to avoid an import loop created when the Hansard
        # search indexes are checked
        from core.models import Person
        from scorecards.models import Category, Entry

        # create the category
        try:
            category = Category.objects.get(slug="hansard-appearances")
        except Category.DoesNotExist:
            raise ImproperlyConfigured("Please create a scorecard category with the slug 'hansard-appearances'")

        # Find all the people we should score for
        people = Person.objects.all().is_mp()
        
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
                entry.remark = "Hardly ever speaks in parliament"
            elif hansard_count < 60:
                entry.score = 0
                entry.remark = "Sometimes speaks in parliament"
            else:
                entry.score = 1
                entry.remark = "Frequently speaks in parliament"
            
            entry.date = datetime.date.today()

            entry.save()

        
        

