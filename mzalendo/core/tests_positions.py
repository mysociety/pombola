import re
import random

from django.conf import settings

from django.core import mail
from django.core import exceptions
from django_webtest import WebTest
from core         import models
from django.test.client import Client
from django.contrib.auth.models import User

from django_date_extensions.fields import ApproximateDate


class PositionTest(WebTest):
    def setUp(self):
        self.person = models.Person(
            legal_name = 'Test Person',
            slug       = 'test-person',
        )
        self.person.save()
        
        self.organisation_kind = models.OrganisationKind(
            name = 'Foo',
            slug = 'foo',
        )
        self.organisation_kind.save()

        self.organisation = models.Organisation(
            name = 'Test Org',
            slug = 'test-org',
            kind = self.organisation_kind,
        )
        self.organisation.save()
        
    def test_unicode(self):
        """Check that missing attributes don't crash"""
        
        position = models.Position(
            person = self.person,
        )
        self.assertEqual( str(position), 'Test Person (??? at ???)' )

    
    def test_sorting(self):
        """Check that the sorting is as expected"""
        
        position_dates = [
            # start_date, end_date, 
            ( 'future',   'future', ),
            ( 'future',   None,     ),
            ( '2002',     'future', ),
            ( '2001',     'future', ),
            ( None,       'future', ),

            ( 'future',   '2010',   ),
            ( '2010',     None,     ),            
            ( '2002',     '2010',   ),
            ( '2001',     '2010',   ),
            ( None,       '2010',   ),

            ( 'future',   '2009',   ),
            ( '2009',     None,     ),
            ( '2002',     '2009',   ),
            ( '2001',     '2009',   ),
            ( None,       '2009',   ),

            ( '2002',     None,     ),
            ( '2001',     None,     ),            

            ( None,       None,     ),
        ]
        
        # create the positions, store the config in the notes and create a list to compare against
        position_expected_order = []
        positions_to_save = []
        
        def approx_date_from_entry(entry):
            if entry is None:
                return None
            if entry == 'future':
                return ApproximateDate(future=True)
            return ApproximateDate(year=int(entry))

        for dates in position_dates:
            note = u"%s -> %s" % dates

            start_date = approx_date_from_entry(dates[0])
            end_date   = approx_date_from_entry(dates[1])

            position_expected_order.append( note )
            positions_to_save.append(
                models.Position(
                    start_date= start_date,
                    end_date  = end_date,
                    note      = note,
                    person    = self.person,
                )
            )
        
        # save all the positions, but shuffle them first
        random.shuffle( positions_to_save )
        for position in positions_to_save:
            position.save()

        # get all the positions from db and check that they are sorted correctly
        positions_from_db = self.person.position_set.all()
        position_actual_order = [ p.note for p in positions_from_db ]

        # print
        # print position_actual_order
        # print
        # print position_expected_order
        # print

        self.maxDiff = None
        self.assertEqual( position_expected_order, position_actual_order )

    def test_have_at_least_one_attribute(self):
        """
        Positions must have a person, and at least one more attribute.
        Otherwise they don't mean anything
        """
        
        pos = models.Position(
            person = self.person,            
        )

        # call this manually so that the validation does not get all confused
        # about it
        pos._set_sorting_dates()

        with self.assertRaises(exceptions.ValidationError):
            pos.full_clean()
        
        # If this does not blow up then it is OK
        pos.organisation = self.organisation
        pos.full_clean()
        

    def test_place_is_required(self):
        """
        Some job titles (like an MP) are meaningless if there is no place
        associated with them.
        """

        title = models.PositionTitle(
            name = 'Test title',
            slug = 'test-title',
        )

        # create position with no place
        position = models.Position(
            person = self.person,
            title  = title,
        )
        position._set_sorting_dates()        
        position.full_clean()
        
        # Change the title to require a place
        title.requires_place = True
        with self.assertRaises(exceptions.ValidationError):
            position.full_clean()

        # give the pos a place and check that it now validates
        position.place = models.Place( name='Test Place', slug='test-place')
        position.full_clean()
