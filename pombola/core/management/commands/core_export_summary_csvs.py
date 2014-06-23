"""Export a collection of summary CSV files for people."""

import csv
import os
import collections

from pombola.core.models import Person

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    args = 'CSV-ROOT'
    help = 'Export a collection of summary CSV files for people.'

    basic_fields = (
        ('A', 'Legal Name', 'name'),
        ('B', 'Slug', 'slug'),
        ('C', 'Gender', 'gender'),
        ('D', 'Date of Birth', 'date_of_birth'),
        ('E', 'Date of Death', 'date_of_death'),
        ('F', 'Summary', 'summary'),
        ('G', 'Email', 'email'),
        ('I', 'Biography', 'biography'),
        ('J', 'National Identity', 'national_identity'),
        ('K', 'Family Name', 'family_name'),
        ('L', 'Given Name', 'given_name'),
        ('M', 'Additional Name', 'additional_name'),
        ('N', 'Honorific Prefix', 'honorific_prefix'),
        ('O', 'Honorific Suffix', 'honorific_suffix'),
    )

    position_fields = (
        ('A', 'Organisation', 'organisation'),
        ('B', 'Place', 'place'),
        ('C', 'Title', 'title'),
        ('D', 'Subtitle', 'subtitle'),
        ('E', 'Category', 'category'),
        ('F', 'Start Date', 'start_date'),
        ('G', 'End Date', 'end_date'),
    )

    def handle(self, *args, **options):

        if len(args) != 1:
            raise CommandError("You must provide a root to place the exported\
CSV files in.")

        csv_root = args[0]

        # Make sure we have somewhere to put all the files
        if not os.path.exists(csv_root):
            os.makedirs(csv_root)

        with open(os.path.join(csv_root, 'summary.csv'), 'wb') as summary_file:
            summary_writer = csv.writer(summary_file)

            # Get the list of people
            people = Person.objects.all().order_by('legal_name')\
                .select_related('contact').select_related('position')

            # Prepare the summary output dict
            summary_output = {}

            # Loop over the basic_fields and set up the empty rows
            for field_key, field_title, field_name in self.basic_fields:
                summary_output[field_key] = [''] * (len(people) + 1)
                summary_output[field_key][0] = field_title

            # Inject the key for the photos.
            summary_output['H'] = [''] * (len(people) + 1)
            summary_output['H'][0] = 'Image URL'

            # Inject the mostly empty row for the Contacts header
            summary_output['P'] = ['CONTACTS']

            # Account for the fact that column 0 is headings
            person_index = 1

            # # Loop over all the people
            for person in people:

                # Loop over the basic_fields
                for field_key, field_title, field_name in self.basic_fields:

                    # Output each basic field to the individual file
                    summary_output[field_key][person_index] =\
                        unicode(getattr(person, field_name)).encode('utf-8')

                    primary_image = person.primary_image()

                    if primary_image != None:
                        image_url = primary_image.url
                    else:
                        image_url = ''

                    summary_output['H'][person_index] =\
                        unicode(image_url).encode('utf-8')

                    contacts = person.contacts.all().order_by('kind')

                    contact_kind = None
                    contact_counter = 1

                    # Loop over the person's contact methods
                    for contact in contacts:

                        # Determine if this is a new contact method title
                        if contact.kind.slug != contact_kind:
                            contact_kind = contact.kind.slug
                            contact_counter = 1

                        # Contacts are at position P.
                        contact_key = 'P-' + contact.kind.slug + '-' + str(contact_counter).zfill(2)

                        # If there isn't already a Contact N row, create one
                        if contact_key not in summary_output:
                            summary_output[contact_key] =\
                                [''] * (len(people) + 1)
                            summary_output[contact_key][0] =\
                                contact.kind.name + ' ' + str(contact_counter)

                        summary_output[contact_key][person_index] =\
                            unicode(contact.value).encode('utf-8')

                        contact_counter += 1

                    positions = person.position_set.all()

                    position_number = 1

                    # Loop over the positions held by this person
                    for position in positions:

                        # Positions are at position Q.
                        position_key = 'Q-' + str(position_number).zfill(3)

                        if position_key not in summary_output:
                            # Inject the mostly empty row for the header
                            summary_output[position_key] = ['POSITION ' + str(position_number)]

                            # Loop over the position_fields and set up the empty rows
                            for field_key, field_title, field_name in self.position_fields:
                                summary_output[position_key + '-' + field_key] =\
                                    [''] * (len(people) + 1)
                                summary_output[position_key + '-' + field_key][0] =\
                                    field_title

                        position_number += 1

                        # Loop over the position_fields
                        for field_key, field_title, field_name in self.position_fields:

                            summary_output[position_key + '-' + field_key][person_index] =\
                                unicode(getattr(position, field_name)).encode('utf-8')

                print "Completed person " + str(person_index) + " of " + str(len(people))

                # Increment the person index counter
                person_index += 1

            # Sort the output
            sorted_output = collections.OrderedDict(sorted(summary_output.items()))

            # Write all the outputs
            for row_title, row_content in sorted_output.items():
                summary_writer.writerow(row_content)

        print "Done! Exported CSV of " + str(len(people)) + "people."

