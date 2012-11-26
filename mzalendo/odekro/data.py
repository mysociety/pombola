#!/usr/bin/env python

import os
import sys
import time
import base64
import json

from django.core.files.base import ContentFile
from django.contrib.contenttypes.models import ContentType, ContentTypeManager
from django.template.defaultfilters import slugify

from django_date_extensions.fields import ApproximateDateField, ApproximateDate

from images.models import Image
from core.models import PlaceKind, OrganisationKind, PositionTitle
from core.models import Place, Person, Organisation, Position
from info.models import InfoPage
from hansard.models import Venue, Source, Sitting, Entry



from odekro.models  import MP, HansardEntry
from utils import split_name, convert_date, legal_name

KINDS = ((PlaceKind, 'constituency'),
         (PositionTitle, 'mp'),
         (PositionTitle, 'member'),
         (OrganisationKind, 'party'),
         (OrganisationKind, 'national'))

constituency_kind, mp_job_title, member_job_title, party_kind, national = \
    [clz.objects.get_or_create(name=s.title(), slug=s)[0] for clz, s in KINDS]

parliament, _ = Organisation.objects.get_or_create(name='Ghana Parliament',
                                                   slug='parliament',
                                                   kind=national)

# "Party": "NPP", 
# "Occupation/Profession": "Lawyers", 
# "Name": "Anyimadu-Antwi, Kwame", 
# "url": "details.php?id=76", 
# "Date of Birth": "April 12, 1962", 
# "Image": "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", 
# "Votes Obtained": "36, 809 votes out of the 54, 407 valid votes cast = 67.7%", 
# "Highest Education": "LLM (Intellectual Property Law) University of London, UK, 2005, BL (GSL) 1995", 
# "Marital Status": "Married (with four children)", 
# "Religion": "Christianity (Presbyterian)", 
# "Hometown": "Patriensa, Ashanti Region", 
# "Last Employment": "Lecturer, KNUST", 
# "Constituency": "Asante Akim North", 
# "Region": "Ashanti"

MP_FIELDS = ['Party', 'Occupation/Profession', 'Name', 'Date of Birth',
             'Votes Obtained', 'Image', 'Marital Status', 'Religion',
             'Hometown', 'Last Employment', 'Constituency', 'Region',
             'Highest Education', 'Gender', 'Summary']



def add_mps_from_json(content):
    for obj in json.loads(content):
        add_mp(obj)

def add_mp(obj):
    party, occupation, name, dob, votes, image, \
    marital_status, religion, hometown, last_employment, constituency, \
    region, education, gender, summary = [obj.get(k, '') for k in MP_FIELDS]

    try:
        last, first, middle, title = split_name(name)
    except:
        print ">>> Error splitting name:", name
        return
    
    legal = legal_name(last, first, middle)
    slug = slugify(legal)

    person, _ = Person.objects.get_or_create(slug=slug)

    if dob:
        dob = convert_date(dob)
        # TODO: investigate using a datetime.date object
        person.date_of_birth = ApproximateDate(year=dob.year, month=dob.month, day=dob.day)
        
    person.title = title
    person.legal_name = legal
    person.summary = summary
    person.gender = gender.lower() or 'm'
    if summary:
        person.can_be_featured = True
    person.save()

    constituency, _ = Place.objects.get_or_create(name=constituency, 
                                                  slug=slugify(constituency), 
                                                  kind=constituency_kind)

    party, _ = Organisation.objects.get_or_create(name=party,
                                                  slug=slugify(party),
                                                  kind=party_kind)

    # add to party
    party_position, _ = Position.objects.get_or_create(person=person,
                                   title=member_job_title,
                                   organisation=party)
    # add to parliament (as mp)
    mp_position, _ = Position.objects.get_or_create(person=person,
                                   title=mp_job_title,
                                   organisation=parliament,
                                   place=constituency)
    
    mp, _ = MP.objects.get_or_create(person=person,
                                  party_position=party_position,
                                  parliament_position=mp_position)
    mp.first_name  = first
    mp.middle_name = middle
    mp.last_name   = last

    mp.occupation = occupation
    mp.marital_status = marital_status
    mp.hometown = hometown
    mp.education = education
    mp.religion = religion
    mp.last_employment = last_employment[:150]
    mp.votes_obtained = votes

    mp.save()

    add_person_image(person, base64.decodestring(image))

def add_person_image(person, image):
    person_image = Image(content_object=person, source=person.slug)
    person_image.image.save(name='thumbnail',
                            content=ContentFile(image))

def add_info_page(slug, title, content):
    try:
        page = InfoPage.objects.get(slug=slug)
    except InfoPage.DoesNotExist:
        page = InfoPage(slug=slug)

    page.title = title
    page.content = unicode(content, 'utf-8')
    return page.save()


def add_hansard(head, entries):
    venue = Venue.objects.get_or_create(
                    slug='parliament-house', 
                    name='Parliament House')[0]
    xs = (head['series'], head['volume'], head['number'])
    source = Source.objects.get_or_create(
                    name='Bound Volume - SER %d VOL. %d No. %d' % xs,
                    date=head['date'])[0]

    adjournment = entries.pop(-1)

    sitting = Sitting.objects.get_or_create(
                        source=source, 
                        venue=venue, 
                        start_date=head['date'],
                        start_time=head['time'],
                        end_date=head['date'],
                        end_time=adjournment['time'])[0]
    entry = None
    while len(entries):
        entry = entries.pop(0)
        if entry['kind'] == 'chair':
            break
    counter = 0
    add_hansard_entry(venue, source, sitting, entry, counter)
    while len(entries):
        counter += 1
        add_hansard_entry(venue, source, sitting, entries.pop(0), counter)


def add_hansard_entry(venue, source, sitting, obj, counter):
    kind = entry_kind(obj)
    entry = Entry.objects.get_or_create(
                    type=kind,
                    sitting=sitting,
                    page_number=obj.get('column', None),
                    speaker_name=obj.get('name', ''),
                    content=obj.get(kind, ''),
                    defaults=(dict(text_counter=counter)))[0]
    entry.text_counter = counter
    entry.save()
    print "%s [%s]: %s (%s)"%(entry.sitting.start_date, obj['kind'], entry.speaker_name, obj.get('section','-'))
    return HansardEntry.objects.get_or_create(
                      sitting=sitting,
                      entry=entry,
                      time=obj.get('time', None),
                      section=obj.get('section', ''),
                      column=obj.get('column', 0))[0]

def entry_kind(entry):
    kind = entry['kind']
    return kind if kind in ['heading', 'scene', 'speech'] else 'other'


# def import_to_db2(objects):
#     for obj in objects:
        
#         member_id = obj['MemberID']
#         image_link = obj["ImageLink"]
        
#         if not image_link:
#             continue

#         try:
#             person = models.Person.objects.get(original_id=member_id)
#         except models.Person.DoesNotExist:
#             print "Could not find %s - ignoring" % person
#             continue

#         url = 'http://mzalendo.com/Images/%s' % image_link


#         source_string = "Original Mzalendo.com website (%s)" % image_link

#         # check to see if this photo has already been used
#         if Image.objects.filter(source=source_string).count():
#             print "Skipping %s - image already used" % person
#             continue

#         print "Fetching image for '%s': '%s'" % ( person, url )
#         person_image = Image(
#             content_object = person,
#             source = source_string,
#         )
#         person_image.image.save(
#             name    = image_link,
#             content = ContentFile( urllib.urlopen( url ).read() ),
#         )

#         # break
#         time.sleep(2)

# def not_implemented():
#     phone_kind, _   = ContactKind.objects.get_or_create(slug='phone', name='Phone')
#     address_kind, _ = ContactKind.objects.get_or_create(slug='address', name='Address')
#     email_kind, _ = ContactKind.objects.get(slug='email', name='Email')

#     # do the contact details
#     #  'Phone': '221291',
#     #  'PhysicalAddress': '',
#     #  'PostalAddress': '',
#     #  'Email': '',

#     content_type = ContentType.objects.get_for_model(person)

#     if obj.get('Phone'):
#         models.Contact.objects.get_or_create(
#             content_type=content_type,
#             object_id=person.id,
#             value=obj['Phone'],
#             kind=phone_kind
#         )

#     if obj.get('PhysicalAddress'):
#         models.Contact.objects.get_or_create(
#             content_type=content_type,
#             object_id=person.id,
#             value=obj['PhysicalAddress'],
#             kind=address_kind,
#             note="physical address",
#         )

#     if obj.get('PostalAddress'):
#         models.Contact.objects.get_or_create(
#             content_type=content_type,
#             object_id=person.id,
#             value=obj['PostalAddress'],
#             kind=address_kind,
#             note="postal address",
#         )

#     if obj.get('Email'):
#         models.Contact.objects.get_or_create(
#             content_type=content_type,
#             object_id=person.id,
#             value=obj['Email'],
#             kind=email_kind,
#         )



