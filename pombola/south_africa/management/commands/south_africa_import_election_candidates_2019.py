"""
Imports ZA provincial and national election candidates using the 2019
IEC spreadsheet format.
"""

import re
import sys
import unicodecsv
import string
import datetime
from optparse import make_option
from pombola.core.models import (
    Organisation,
    OrganisationKind,
    Person,
    Position,
    PositionTitle,
    AlternativePersonName,
)
from django.core.management.base import NoArgsCommand
from django.db.models import Q
from django.db.utils import IntegrityError
from django.utils.text import slugify

from django_date_extensions.fields import ApproximateDate

from haystack.query import SearchQuerySet

final_candidate_list_date = ApproximateDate(year=2019, month=4, day=23)
month_before_final_list_date = ApproximateDate(year=2019, month=3)


party_to_object = {}
list_to_object = {}
position_to_object = {}
YEAR = "2019"
COMMIT = False

csv_files = [
    'National.csv',
    'Provincial-EC.csv',
    'Provincial-FS.csv',
    'Provincial-GP.csv',
    'Provincial-KZN.csv',
    'Provincial-LIM.csv',
    'Provincial-MP.csv',
    'Provincial-NC.csv',
    'Provincial-NW.csv',
    'Provincial-WC.csv',
]

candidates = []

for candidates_csv in csv_files:
    with open("pombola/south_africa/data/elections/2019/" + candidates_csv, "rb") as csvfile:
        csv = unicodecsv.DictReader(csvfile)
        [candidates.append(row) for row in csv]

parties_csv = "pombola/south_africa/data/elections/2019/parties.csv"
party_mapping = {}
with open(parties_csv, "rb") as csvfile:
    csv = unicodecsv.DictReader(csvfile)
    for row in csv:
        party_mapping[row["name_in_candidates_file"]] = row["slug"]

errors = []


def check_or_create_positions():
    """Checks whether positions exist, otherwise create them"""
    num_append = {
        "1": "st",
        "2": "nd",
        "3": "rd",
        "4": "th",
        "5": "th",
        "6": "th",
        "7": "th",
        "8": "th",
        "9": "th",
        "0": "th",
    }
    positions = range(1, 201)

    for p in positions:
        position_name = str(p) + num_append[str(p)[-1]] + " Candidate"
        position_slug = str(p) + num_append[str(p)[-1]] + "_candidate"
        position_object, _ = PositionTitle.objects.get_or_create(
            slug=position_slug, defaults={"name": position_name}
        )
        position_to_object[unicode(p)] = position_object


def get_list(listname, listslug):
    """Returns the organisation object for a list"""
    if listname in list_to_object:
        return list_to_object[listname]

    organisationkind, _ = OrganisationKind.objects.get_or_create(
        slug="election-list", name="Election List"
    )
    listobject, _ = Organisation.objects.get_or_create(
        slug=listslug, name=listname, kind=organisationkind
    )
    list_to_object[listname] = listobject
    return listobject


def get_party(partyname):
    """Returns the organisation object for a party"""
    partyname = re.sub(r"\s+", " ", partyname)
    # if the party has already been worked with, return that
    if partyname in party_to_object:
        return party_to_object[partyname]

    party_slug = party_mapping.get(partyname)
    if not party_slug:
        return False

    party = Organisation.objects.get(slug=party_slug)
    if party:
        party_to_object[partyname] = party
        return party_to_object[partyname]
    else:
        return False


def save_match(
    person,
    party_name,
    list_position,
    import_list_name,
    person_list_firstnames,
    person_list_surname,
    id_number,
):
    """Save imported details about a person who already exists"""
    # get the list to add the person to
    import_list_name = string.replace(import_list_name, ":", "")
    party = get_party(party_name)
    party_parts = string.split(party.name, " (")
    listname = party_parts[0] + " " + import_list_name + " Election List " + YEAR
    listslug = slugify(
        party.slug
        + "-"
        + string.replace(import_list_name.lower(), " ", "-")
        + "-election-list-"
        + YEAR
    )
    list_object = get_list(listname, listslug)

    # get the position title
    positiontitle = position_to_object[list_position]

    # check if we have distinct family/given names on record - if we do
    # we assume these are absolutely correct and so if they do not match
    # the import values the match is considered incorrect
    if person.given_name == "" and person.family_name == "":
        person.given_name = person_list_firstnames.title()
        person.family_name = person_list_surname.title()
        if COMMIT:
            print "- updating given_name/family_name"
            person.save()
        else:
            print "* would update blank given_name/family_name"
    elif string.replace(person_list_firstnames.lower(), "-", " ") != string.replace(
        person.given_name.lower(), "-", " "
    ) or string.replace(person_list_surname.lower(), "-", " ") != string.replace(
        person.family_name.lower(), "-", " "
    ):
        print "- but names do not match existing given_name/family_name, ignoring"
        return False

    # get the person's current party to compare whether these have changed
    # we assume that a person on an election list should not be a member
    # more than one party - so we end memberships that do not match the list
    foundcorrectparty = False
    for p in person.parties():
        if p == party:
            foundcorrectparty = True
        else:
            # end the membership
            now = datetime.date.today()
            now_approx = repr(
                ApproximateDate(year=now.year, month=now.month, day=now.day)
            )
            position = Position.objects.get(
                Q(person=person),
                Q(organisation=p),
                Q(title__slug="member"),
                Q(start_date__lte=now_approx),
                (Q(sorting_end_date_high__gte=now_approx) | Q(end_date="")),
            )
            position.end_date = month_before_final_list_date
            if COMMIT:
                print "- ending %s party position" % position.organisation
                position.save()
            else:
                print "* would end %s party position" % position.organisation

    if COMMIT and not foundcorrectparty:
        print "- creating %s party position" % party
        # get the member title
        member = PositionTitle.objects.get(name="Member")
        # add the correct membership
        position = Position.objects.get_or_create(
            person=person,
            organisation=party,
            start_date=month_before_final_list_date,
            title=member,
            category="political",
        )

    # check whether the list name matches the recorded name
    if (
        person_list_firstnames + " " + person_list_surname
    ).lower() != person.legal_name.lower():
        # set the new name as the person name and record the old as an
        # alternative name
        new_name = (person_list_firstnames + " " + person_list_surname).title()
        if COMMIT:
            print "- updating person name from %s to %s" % (person.legal_name, new_name)
            AlternativePersonName.objects.get_or_create(
                person=person, alternative_name=person.name
            )
            person.legal_name = new_name
            person.save()
        else:
            print "* would update person legal_name from %s to %s" % (
                person.legal_name,
                new_name,
            )

    if COMMIT:
        person.identifiers.get_or_create(scheme='elections_2019', identifier=id_number)

    # add the actual membership of the list organisation. Note no end date
    # is set at this point. This should probably be the date of the election
    # but it is unclear whether setting this immediately would cause issues
    # if viewed on the election date or immediately afterwards
    if COMMIT:
        print "- creating candidate position"
        position = Position.objects.get_or_create(
            person=person,
            organisation=list_object,
            start_date=final_candidate_list_date,
            title=positiontitle,
            category="political",
        )

    return True


def add_new_person(
    party_name,
    list_position,
    import_list_name,
    person_list_firstnames,
    person_list_surname,
    id_number,
):
    """Create a new person with appropriate positions"""

    if not COMMIT:
        print "would create new entry"
        return

    print "creating"
    # get the list to add the person to
    import_list_name = string.replace(import_list_name, ":", "")
    party = get_party(party_name)
    party_parts = string.split(party.name, " (")
    listname = party_parts[0] + " " + import_list_name + " Election List " + YEAR
    listslug = slugify(
        party.slug
        + "-"
        + string.replace(import_list_name.lower(), " ", "-")
        + "-election-list-"
        + YEAR
    )
    list_object = get_list(listname, listslug)

    # get the position title
    positiontitle = position_to_object[list_position]

    slug = slugify(person_list_firstnames + " " + person_list_surname)

    try:
        # create the person
        person, _ = Person.objects.get_or_create(
            legal_name=(person_list_firstnames + " " + person_list_surname).title(),
            given_name=person_list_firstnames.title(),
            family_name=person_list_surname.title(),
            slug=slug,
        )
    except IntegrityError as e:
        errors.append(e)
        person = Person.objects.get(slug=slug)

    # add to the party
    member = PositionTitle.objects.get(name="Member")
    position, _ = Position.objects.get_or_create(
        person=person, organisation=party, title=member, category="political"
    )

    person.identifiers.get_or_create(scheme='elections_2019', identifier=id_number)

    # add the actual membership of the list organisation. Note no end date
    # is set at this point. This should probably be the date of the election
    # but it is unclear whether setting this immediately would cause issues
    # if viewed on the election date or immediately afterwards
    position, _ = Position.objects.get_or_create(
        person=person,
        organisation=list_object,
        start_date=final_candidate_list_date,
        title=positiontitle,
        category="political",
    )


def process_search(firstnames, surname, party, list_position, list_name, url, id_number):
    """Process a search based on the search string passed via url"""
    search = SearchQuerySet().models(Person).filter(text=url)
    if len(search) > 1:
        name = (firstnames + " " + surname).title()
        search = [s for s in search if s.object and s.object.legal_name == name]
    if len(search) == 1 and search[0].object:
        print "match", search[0].object.name
        return save_match(
            search[0].object, party, list_position, list_name, firstnames, surname, id_number
        )
    else:
        return False


# Search 1
def search_full_name(firstnames, surname, party, list_position, list_name, id_number):
    searchurl = '"' + (firstnames + " " + surname) + '"'
    return process_search(
        firstnames, surname, party, list_position, list_name, searchurl, id_number
    )


# Search 2
def search_reordered(firstnames, surname, party, list_position, list_name, id_number):
    searchurl = '"' + (firstnames + " " + surname) + '"~4'
    return process_search(
        firstnames, surname, party, list_position, list_name, searchurl, id_number
    )


# Search 3
def search_first_names(firstnames, surname, party, list_position, list_name, id_number):
    names = firstnames.split(" ")
    if len(names) == 1:
        # Already covered by search 1
        return False
    for name in names:
        searchurl = '"' + (name + " " + surname) + '"'
        if process_search(
            firstnames, surname, party, list_position, list_name, searchurl, id_number
        ):
            return True
    return False


# Search 4
def search_initials(firstnames, surname, party, list_position, list_name, id_number):
    names = firstnames.split(" ")
    initials = ""
    for name in names:
        if name[:1] == "A":
            continue
        initials += name[:1] + ". "
    if not initials:
        return False
    searchurl = '"' + (initials + surname) + '"'
    return process_search(
        firstnames, surname, party, list_position, list_name, searchurl, id_number
    )


# Search 5
def search_initials_alt(firstnames, surname, party, list_position, list_name, id_number):
    names = firstnames.split(" ")
    initials = ""
    for name in names:
        if name[:1] == "A":
            continue
        initials += name[:1] + "."
    if not initials:
        return False
    searchurl = '"' + (initials + " " + surname) + '"'
    return process_search(
        firstnames, surname, party, list_position, list_name, searchurl, id_number
    )


# Search 6
def search_misspellings(firstnames, surname, party, list_position, list_name, id_number):
    names = firstnames.split(" ")
    first = ""
    for name in names:
        first += name + "~ AND "
    searchurl = first + surname
    return process_search(
        firstnames, surname, party, list_position, list_name, searchurl, id_number
    )


def search(firstnames, surname, party, list_position, list_name, id_number):
    """Attempt varius approaches to matching names"""
    print "Looking at %s %s:" % (firstnames, surname),

    existing = Person.objects.filter(
        given_name__iexact=firstnames, family_name__iexact=surname
    )
    if len(existing) == 1:
        print "match existing", existing[0].name
        if save_match(
            existing[0], party, list_position, list_name, firstnames, surname, id_number
        ):
            return True

    if search_full_name(firstnames, surname, party, list_position, list_name, id_number):
        return True
    if search_reordered(firstnames, surname, party, list_position, list_name, id_number):
        return True
    if search_first_names(firstnames, surname, party, list_position, list_name, id_number):
        return True
    if search_initials(firstnames, surname, party, list_position, list_name, id_number):
        return True
    if search_initials_alt(firstnames, surname, party, list_position, list_name, id_number):
        return True
    if search_misspellings(firstnames, surname, party, list_position, list_name, id_number):
        return True
    return False


class Command(NoArgsCommand):
    """Import South African national and provincial election candidates"""

    help = (
        "Import csv file of South African national and provincial election candidates"
    )

    option_list = NoArgsCommand.option_list + (
        make_option(
            "--commit",
            action="store_true",
            help="Actually commit person changes to the database (new positions/orgs always created)",
        ),
    )

    def handle_noargs(self, **options):
        global COMMIT
        COMMIT = options["commit"]

        # check all the parties exist
        missingparties = set()
        for row in candidates:
            party_name = row["Party name"]
            if not get_party(party_name):
                missingparties.add(party_name)
        if missingparties:
            for party in sorted(missingparties):
                print "Missing party:", party
            sys.exit(1)

        # check whether the positions exist, otherwise create them
        check_or_create_positions()

        for row in candidates:
            party_name = row["Party name"].strip()
            list_type = row["List type"].strip()
            order_number = row["Order number"].strip()
            full_names = row["Full names"].strip()
            surname = row["Surname"].strip()
            id_number = row['IDNumber'].strip()

            if not search(full_names, surname, party_name, order_number, list_type, id_number):
                add_new_person(party_name, order_number, list_type, full_names, surname, id_number)

        if errors:
            print("ERRORS:")
            for error in errors:
                print(error)
