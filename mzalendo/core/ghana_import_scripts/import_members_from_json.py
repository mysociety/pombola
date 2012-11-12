#!/usr/bin/env python

import os
import sys
import re

# Horrible boilerplate - there must be a better way :)
sys.path.append(
    os.path.abspath(
        os.path.dirname(__file__) + '../../..'
    )
)


import datetime
import json
from pprint import pprint
from django.template.defaultfilters import slugify
from core import models
from django_date_extensions.fields import ApproximateDateField, ApproximateDate
from django.contrib.contenttypes.models import ContentType, ContentTypeManager

import name_to_first_last

mp_job_title      = models.PositionTitle.objects.get(slug="mp")
member_job_title  = models.PositionTitle.objects.get(slug="member")

phone_kind   = models.ContactKind.objects.get(slug='phone')
address_kind = models.ContactKind.objects.get(slug='address')
email_kind   = models.ContactKind.objects.get(slug='email')

objects           = simplejson.loads( sys.stdin.read() )

for obj in objects:

    #Relevant fields are:
    # Name
    # Constituency
    # Region
    # Party
    # Occupation/Profession
    # Parliamentary Seat
    # Date of Birth
    # Hometown
    # Highest Education
    # Last Employment
    # Marital Status
    # Religion
    # Votes Obtained

    # pprint( obj )
    # break
         
    # {'Active': 'true',
    #  'DateOfBirth': '1961-10-26',
    #  'Duties': 'Leader Of The Official Opposition',
    #  'Email': '',
    #  'Fullnames': 'Kenyatta, Uhuru Muigai',
    #  'Gender': 'M',
    #  'ImageLink': 'kenyatta_u.jpg',
    #  'MemberID': '1',
    #  'OtherEducation': '',
    #  'Phone': '221291',
    #  'PhysicalAddress': '',
    #  'PostalAddress': '',
    #  'PrimaryEducation': 'Kenyatta Primary School',
    #  'Profile': 'Employment History: \r\n1985-2001: Chairman, Chief Executive and Director in varying companies,\r\n1998-2003: Council Member, Jomo Kenyatta University of Agriculture & Technology,\r\n1999-2001: Chairman, Kenya Tourist Board,\r\n2000-2001: Chairman, Disaster Emergency Response Committee,\r\n2001-2002: KANU Nominated Member of Parliament',
    #  'SecondaryEducation': u'1979: A-Level St Mary\xe2\x80\x99s School 1985 B.A.',
    #  'StatusID': '2',
    #  'UniversityEducation': 'Economics and Political Science Amhrest College,USA '}
    

    try:
        (last, first, middle,gender) = name_to_first_last.conversions[obj['Name']]
    except:
        print obj['Name']
        continue
    
    slug = slugify(first + ' ' + last)

    try:
        db_obj = models.Person.objects.get( slug = slug )
    except models.Person.DoesNotExist:
        db_obj = models.Person( slug = slug )


    dob = obj.get('Date Of Birth')
    if dob: # 
        #dob = re.sub( '-01-01', '-00-00', dob ) # 1 Jan happens too often - assume it means that month and day unknown
        # print dob
        dobdt = datetime.datetime(dob)
        print dobdt
        (year, month, day) = re.split( '-', dob )
        if int(year):
            db_obj.date_of_birth = ApproximateDate( year=int(year), month=int(month), day=int(day) )
        
    #db_obj.original_id = obj['MemberID']

    db_obj.first_name  = first
    db_obj.middle_name = middle
    db_obj.last_name   = last
    
    db_obj.gender = gender

    #uncomment!!!!
    #db_obj.save()
    print db_obj
    
    # do the contact details
    #  'Phone': '221291',
    #  'PhysicalAddress': '',
    #  'PostalAddress': '',
    #  'Email': '',

    content_type = ContentType.objects.get_for_model(db_obj)

    if obj.get('Phone'):
        models.Contact.objects.get_or_create(
            content_type=content_type,
            object_id=db_obj.id,
            value=obj['Phone'],
            kind=phone_kind
        )

    if obj.get('PhysicalAddress'):
        models.Contact.objects.get_or_create(
            content_type=content_type,
            object_id=db_obj.id,
            value=obj['PhysicalAddress'],
            kind=address_kind,
            note="physical address",
        )

    if obj.get('PostalAddress'):
        models.Contact.objects.get_or_create(
            content_type=content_type,
            object_id=db_obj.id,
            value=obj['PostalAddress'],
            kind=address_kind,
            note="postal address",
        )

    if obj.get('Email'):
        models.Contact.objects.get_or_create(
            content_type=content_type,
            object_id=db_obj.id,
            value=obj['Email'],
            kind=email_kind,
        )



