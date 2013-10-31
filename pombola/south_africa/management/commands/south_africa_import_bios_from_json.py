from warnings import warn
import json

from django.core.management.base import LabelCommand, CommandError

from pombola.core.models import Person

# Expected JSON is an array of entries:
#
# [
#     {
#         "name": "John Smith",
#         "bio": "Blah blah"
#     },
#     ....
# ]
#
# ``name`` should match the Person's ``legal_name`` and ``bio`` is stored in their summary field.



class Command(LabelCommand):
    help = 'Set profiles (in summary field)'
    args = '<profile JSON file>'

    def handle_label(self,  input_filename, **options):

        input_entries = json.loads( open(input_filename, 'r').read() )

        for entry in input_entries:

            try:
                person = Person.objects.get(legal_name=entry['name'])
            except Person.DoesNotExist:
                warn("Could not find person matching '%s'" % entry['name'])
                continue

            print "Setting summary for '%s'" % person

            bio = entry['bio']
            bio = bio.replace('\n', '\n\n')
            person.summary = bio
            person.save()
