'''
Imports ZA provincial and national election candidates using the 2014
IEC spreadsheet format.
'''

import os
import sys
import unicodecsv
import json
import string
from optparse import make_option
from pombola.core.models import (Organisation, OrganisationKind,
                         Person, Position,
                         PositionTitle, AlternativePersonName)
from django.core.management import call_command
from django.core.management.base import NoArgsCommand, CommandError
from django.utils import encoding

from django.core.exceptions import ObjectDoesNotExist

from django_date_extensions.fields import ApproximateDateField, ApproximateDate

from haystack.query import SearchQuerySet

party_to_object = {}
list_to_object = {}
position_to_object = {}
YEAR=''

def check_or_create_positions():
    '''Checks whether positions exist, otherwise create them'''
    num_append= {'1': 'st', '2':'nd', '3':'rd', '4':'th', '5':'th', '6':'th', '7':'th', '8':'th', '9':'th', '0':'th'}
    positions = range(1, 201)

    for p in positions:
        position_name = str(p) + num_append[str(p)[-1]] + ' Candidate'
        position_slug = str(p) + num_append[str(p)[-1]] + '_candidate'
        position_object, _ = PositionTitle.objects.get_or_create(
            slug=position_slug,
            name=position_name)
        position_to_object[unicode(p)] = position_object

def get_list(listname, listslug):
    '''Returns the organisation object for a list'''
    if listname in list_to_object:
        return list_to_object[listname]

    organisationkind, _ = OrganisationKind.objects.get_or_create(
        slug='election-list',
        name='Election List')
    listobject, _ = Organisation.objects.get_or_create(
        slug=listslug,
        name=listname,
        kind=organisationkind,)
    list_to_object[listname] = listobject
    return listobject

def get_party(partyname):
    '''Returns the organisation object for a party'''
    #if the party has already been worked with, return that
    if partyname in party_to_object:
        return party_to_object[partyname]

    #check if the party exists in the database
    parties = Organisation.objects.filter(name__icontains=partyname, kind__slug='party')
    if len(parties) == 1:
        party_to_object[partyname] = parties[0]
        return party_to_object[partyname]
    else:
        return False

def save_match(person, party_name, list_position, import_list_name, person_list_firstnames, person_list_surname):
    '''Save imported details about a person who already exists'''
    #get the list to add the person to
    import_list_name = string.replace(import_list_name, ':', '')
    party = get_party(party_name)
    party_parts = string.split(party.name, ' (')
    listname = party_parts[0]+' '+import_list_name+' Election List '+YEAR
    listslug = party.slug+'-'+string.replace(import_list_name.lower(),' ','-')+'-election-list-'+YEAR
    list_object = get_list(listname, listslug)

    #get the position title
    positiontitle = position_to_object[list_position]

    #get the person's current party to compare whether these have changed
    #we assume that a person on an election list should not be a member
    #more than one party - so we end memberships that do not match the list
    #start/end dates are assumed as March 2014 (TODO: this will need to
    #change if the script is used for later elections)
    foundcorrectparty = False
    for p in person.parties():
        if p == party:
            foundcorrectparty = True
        else:
            #end the membership
            position = Position.objects.get(person = person, organisation = p)
            position.end_date = ApproximateDate(year=2014, month=3)
            position.save()

    if not foundcorrectparty:
        #get the member title
        member = PositionTitle.objects.get(name='Member')
        #add the correct membership
        position = Position.objects.get_or_create(
            person = person,
            organisation = party,
            start_date = ApproximateDate(year=2014, month=3), #TODO - correct for later use
            title = member,
            category = 'political')

    #check whether the list name matches the recorded name
    if (person_list_firstnames+' '+person_list_surname).lower() != person.legal_name.lower():
        #set the new name as the person name and record the old as an
        #alternative name
        AlternativePersonName.objects.get_or_create(person = person, alternative_name = person.name)
        person.legal_name = (person_list_firstnames+' '+person_list_surname).title()
        person.save()

    #check if we have distinct family/given names on record
    if person_list_firstnames.lower() != person.given_name.lower():
        person.given_name = person_list_firstnames.title()
        person.save()
    if person_list_surname.lower() != person.family_name.lower():
        person.family_name = person_list_surname.title()
        person.save()

    #add the actual membership of the list organisation. Note no end date
    #is set at this point. This should probably be the date of the election
    #but it is unclear whether setting this immediately would cause issues
    #if viewed on the election date or immediately afterwards
    position = Position.objects.get_or_create(
        person = person,
        organisation = list_object,
        start_date = ApproximateDate(year=2014, month=4, day=22), #set to the date of release of the final candidate lists. TODO - update for subsequent years
        title = positiontitle,
        category = 'political')

def add_new_person(party_name, list_position, import_list_name, person_list_firstnames, person_list_surname):
    '''Create a new person with appropriate positions'''
    print 'Creating', person_list_firstnames, person_list_surname
    #get the list to add the person to
    import_list_name = string.replace(import_list_name, ':', '')
    party = get_party(party_name)
    party_parts = string.split(party.name, ' (')
    listname = party_parts[0]+' '+import_list_name+' Election List '+YEAR
    listslug = party.slug+'-'+string.replace(import_list_name.lower(),' ','-')+'-election-list-'+YEAR
    list_object = get_list(listname, listslug)

    #get the position title
    positiontitle = position_to_object[list_position]

    #create the person
    person , _ = Person.objects.get_or_create(
        legal_name=(person_list_firstnames+' '+person_list_surname).title(),
        given_name = person_list_firstnames.title(),
        family_name = person_list_surname.title(),
        slug = string.replace((person_list_firstnames+' '+person_list_surname).lower(),' ','-'))

    #add to the party
    member = PositionTitle.objects.get(name='Member')
    position , _ = Position.objects.get_or_create(
        person = person,
        organisation = party,
        title = member,
        category = 'political')

    #add the actual membership of the list organisation. Note no end date
    #is set at this point. This should probably be the date of the election
    #but it is unclear whether setting this immediately would cause issues
    #if viewed on the election date or immediately afterwards
    position , _ = Position.objects.get_or_create(
        person = person,
        organisation = list_object,
        start_date = ApproximateDate(year=2014, month=4, day=22), #set to the date of release of the official candidate lists. TODO - update for subsequent years
        title = positiontitle,
        category = 'political')

def process_search(firstnames, surname, party, list_position, list_name, url):
    '''Process a search based on the search string passed via url'''
    search = SearchQuerySet().models(Person).filter(text=url)
    if len(search) == 1 and search[0].object:
        print 'match', search[0].object.name
        save_match(search[0].object, party, list_position, list_name, firstnames, surname)
        return True
    else:
        return False

#Search 1
def search_full_name(firstnames, surname, party, list_position, list_name):
    searchurl = '"'+(firstnames+' '+surname)+'"'
    return process_search(firstnames, surname, party, list_position, list_name, searchurl)

#Search 2
def search_reordered(firstnames, surname, party, list_position, list_name):
    searchurl = '"'+(firstnames+' '+surname)+'"~4'
    return process_search(firstnames, surname, party, list_position, list_name, searchurl)

#Search 3
def search_first_names(firstnames, surname, party, list_position, list_name):
    names = firstnames.split(" ")
    for name in names:
        searchurl = '"'+(name+' '+surname)+'"'
        if process_search(firstnames, surname, party, list_position, list_name, searchurl):
            return True
    return False

#Search 4
def search_initials(firstnames, surname, party, list_position, list_name):
    names = firstnames.split(" ")
    initials=''
    for name in names:
        initials+=name[:1]+'. '
    searchurl = '"'+(initials+surname)+'"'
    return process_search(firstnames, surname, party, list_position, list_name, searchurl)

#Search 5
def search_initials_alt(firstnames, surname, party, list_position, list_name):
    names = firstnames.split(" ")
    initials=''
    for name in names:
        initials+=name[:1]+'.'
    searchurl = '"'+(initials+' '+surname)+'"'
    return process_search(firstnames, surname, party, list_position, list_name, searchurl)

#Search 6
def search_misspellings(firstnames, surname, party, list_position, list_name):
    names = firstnames.split(" ")
    first=''
    for name in names:
        first+=name+'~ AND '
    searchurl = first+surname
    return process_search(firstnames, surname, party, list_position, list_name, searchurl)

def search(firstnames, surname, party, list_position, list_name):
    '''Attempt varius approaches to matching names'''
    if search_full_name(firstnames, surname, party, list_position, list_name):
        return True
    if search_reordered(firstnames, surname, party, list_position, list_name):
        return True
    if search_first_names(firstnames, surname, party, list_position, list_name):
        return True
    if search_initials(firstnames, surname, party, list_position, list_name):
        return True
    if search_initials_alt(firstnames, surname, party, list_position, list_name):
        return True
    if search_misspellings(firstnames, surname, party, list_position, list_name):
        return True
    return False

class Command(NoArgsCommand):
    '''Import South African national and provincial election candidates'''

    help = 'Import csv file of South African national and provincial election candidates'

    option_list = NoArgsCommand.option_list + (
        make_option( '--candidates', '-c', help="The candidates csv file" ),
        make_option( '--year', '-y', help="The year of the election" ),
    )

    def handle_noargs(self, **options):
        global YEAR
        YEAR = options['year']

        if not options['candidates'] or not os.path.exists(options['candidates']):
            print >> sys.stderr, "The candidates file doesn't exist"
            sys.exit(1)

        #check all the parties exist
        with open(options['candidates'], 'rb') as csvfile:
            candidiates = unicodecsv.reader(csvfile)
            missingparties = False
            lastmissingparty = ''
            for row in candidiates:
                if not get_party(row[0]):
                    if row[0] != lastmissingparty:
                        print 'Missing party:', row[0]
                        lastmissingparty = row[0]
                    missingparties = True
            if missingparties:
                sys.exit(1)

        #check whether the positions exist, otherwise create them
        check_or_create_positions()

        with open(options['candidates'], 'rb') as csvfile:
            candidiates = unicodecsv.reader(csvfile)
            for row in candidiates:
                if not search(row[3], row[4], row[0], row[2], row[1]):
                    add_new_person(row[0], row[2], row[1], row[3], row[4])
