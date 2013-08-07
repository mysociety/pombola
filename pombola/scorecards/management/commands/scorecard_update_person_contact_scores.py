import datetime

from django.core.management.base import NoArgsCommand
from django.core.exceptions import ImproperlyConfigured

class Command(NoArgsCommand):
    help = 'Create/update contactability entry for all mps'
    args = ''

    def handle_noargs(self, **options):

        # Imports are here to avoid an import loop created when the Hansard
        # search indexes are checked
        from pombola.core.models import Person
        from pombola.scorecards.models import Category, Entry

        # create the category
        try:
            category = Category.objects.get(slug = "contactability")
        except Category.DoesNotExist:
            raise ImproperlyConfigured("Please create a scorecard category with the slug 'contactability'")

        # Find all the people we should score for
        # TODO - limit to just some people (mps, candidates, etc)
        people = Person.objects.all()
        
        for person in people:
            # count the number of different forms of contact they have - sum them up
            # manually as trying to do the distinct(kind) on the queryset was overly
            # complicated.
            contact_kinds = {}
            for c in person.contacts.all():
                contact_kinds[c.kind.slug] = 1
            
            contact_count = len( contact_kinds.keys() )
        
            # turn the count into a score
            score = -1
            if contact_count >= 3: score = 0
            if contact_count >= 4: score = 1
            
            try:
                entry = person.scorecard_entries.get( category=category )
            except Entry.DoesNotExist:
                entry = Entry(content_object=person, category=category )
            
            entry.date = datetime.date.today()
            entry.score = score

            if score == -1:
                entry.remark = "There are few ways to reach this person"
            elif score == 0:
                entry.remark = "There are some ways to reach this person"
            else:
                entry.remark = "There are many ways to reach this person"

            entry.save()

        
        

