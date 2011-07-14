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

import setup_env

import simplejson
from pprint import pprint
from django.template.defaultfilters import slugify
from core import models
from django_date_extensions.fields import ApproximateDateField, ApproximateDate

import name_to_first_last

mp_job_title      = models.PositionTitle.objects.get(slug="mp")
member_job_title  = models.PositionTitle.objects.get(slug="member")
objects           = simplejson.loads( sys.stdin.read() )

for obj in objects:

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
        (last, first, middle) = name_to_first_last.conversions[obj['Fullnames']]
    except:
        print obj['Fullnames']
        continue
    
    slug = slugify(first + ' ' + last)

    try:
        db_obj = models.Person.objects.get( slug = slug )
    except models.Person.DoesNotExist:
        db_obj = models.Person( slug = slug )


    dob = obj.get('DateOfBirth')
    if dob:
        dob = re.sub( '-01-01', '-00-00', dob ) # 1 Jan happens too often - assume it means that month and day unknown
        # print dob
        (year, month, day) = re.split( '-', dob )
        if int(year):
            db_obj.date_of_birth = ApproximateDate( year=int(year), month=int(month), day=int(day) )
        
    db_obj.original_id = obj['MemberID']

    db_obj.first_name  = first
    db_obj.middle_name = middle
    db_obj.last_name   = last
    
    db_obj.gender = obj['Gender'].lower()

    db_obj.save()

