import re

import unicodecsv as csv

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from pombola.core.models import Organisation, Person, ContactKind


class Command(BaseCommand):
    help = "One-off command to import new emails for National Assembly MPs after the 2019 elections"

    def handle(self, *args, **options):
        na_emails_filename = "pombola/south_africa/data/elections/2019/na-emails.csv"
        committee_emails_filename = (
            "pombola/south_africa/data/elections/2019/committee-emails.csv"
        )

        source = "Data provided by PMG"
        contact_kind_email = ContactKind.objects.get(slug="email")

        # National Assembly
        with open(na_emails_filename) as csvfile:
            rows = csv.DictReader(csvfile)
            for row in rows:
                name = re.sub(r"\s+", " ", row["NAMES"] + " " + row["SURNAME"]).strip()
                emails = [email.strip() for email in row["EMAIL ADDRESS"].split("/")]
                matching_people = Person.objects.filter(
                    Q(legal_name__icontains=name)
                    | Q(alternative_names__alternative_name__iexact=name)
                ).distinct()
                for person in matching_people:
                    for email in emails:
                        _, created = person.contacts.get_or_create(
                            kind=contact_kind_email,
                            value=email,
                            defaults={"source": source, "preferred": True},
                        )
                        if created:
                            print "Added {} to".format(email),
                            print (name)

        # Committees
        with open(committee_emails_filename) as csvfile:
            rows = csv.DictReader(csvfile)
            for row in rows:
                name = row["Name of Committee"].strip()
                email = row["Email address"].strip()
                matching_committees = Organisation.objects.filter(
                    name__iendswith=name, kind__slug="national-assembly-committees"
                )
                if not matching_committees:
                    print ("! No matches for {}".format(name))
                else:
                    committee = matching_committees[0]
                    _, created = committee.contacts.get_or_create(
                        kind=contact_kind_email,
                        value=email,
                        defaults={"source": source, "preferred": True},
                    )
                    if created:
                        print "Added {} to {}".format(email, name)
