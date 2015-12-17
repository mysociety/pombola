#!/usr/bin/env python

import os
import sys

# Horrible boilerplate - there must be a better way :)
sys.path.append(
    os.path.abspath(
        os.path.dirname(__file__) + '../../..'
    )
)
sys.path.append(
    os.path.abspath(
        os.path.dirname(__file__) + '../../../..'
    )
)


import csv
import pprint
import re

from pombola.projects.models import Project
from pombola.core.models import Place

from django.contrib.gis.geos import Point


def main():
    pi = ProjectImporter()
    pi.import_from_csv_file( sys.argv[1] )


class ProjectImporter(object):
    constituency_qs = Place.objects.filter(kind__slug='constituency')
    not_found_constituencies = set()
    
    # Use this to rename the constituencies to suit what we have in our database
    constituency_renames = {
        # "Alego Usonga": 'Alego',
        # "Buret", # is a division
        # "Kabete", # not found
        # "Kajiado South", # found 'North' and 'Central'
        # "Kipiripiri",
        # "Maragua", # not found
        # "Mukwurweini", # 'Mukurweini' division
        "Cherengany":              "Cherengani",
        "Dagoreti":                "Dagoretti",
        "Igembe North (Ntonyiri)": "Igembe North",
        "Kisumu Rural":            "Kisumi Rural",
        "Kisumu Town East":        "Kisumi Town East",
        "Kisumu Town West":        "Kisumi Town West",
        "Mt. Elgon":               "Mt Elgon",
        "North Mugirango":         "North Mugirango Borabu",
        "North-Horr":              "North Horr",
        "Ol'Kalou":                "Ol' Kalou",
    }
  
    def import_from_csv_file( self, csv_file_name ):
        """Import data from a csv file with the expected fieldnames"""
        
        csv_file = open(csv_file_name)
        
        self.reader = csv.DictReader( csv_file )        
        
        for row in self.reader:
            # try:
            self.import_row( row )
            # except Exception as inst:
            #     print( "Issue %s on csv line %u: %s" % ( repr(inst), self.reader.line_num, inst ))
            # 
            # # break
        
        if len( self.not_found_constituencies ):
            print "The following constituencies could not be found"
            pprint.pprint( self.not_found_constituencies )
        
        
    def import_row(self, row):

        # print "Adding %s" % row['Project name']

        # Numbers exports CSV using 'Nil' for empty fields. Change to empty string.
        for key, value in row.items():
            if value == 'Nil': row[key] = ''
        
        # change money values to floats
        for key in ['estimated cost','Total Amount']:
            try:
                row[key] = float( row[key] )
            except:
                row[key] = 0
        
        data = dict(
            cdf_index           = int(row['index']),
            project_name        = row['Project name'],
            location_name       = row['Location'],
            sector              = row['Sector'],
            mtfe_sector         = row['MTFE Sector'],
            econ1               = row['Econ1'],
            econ2               = row['Econ2'],
            activity_to_be_done = row['activity to bedone'],
            expected_output     = row['expected output'],
            status              = row['implementation status'],
            remarks             = row['remarks'][:400],
            estimated_cost      = row['estimated cost'],
            total_cost          = row['Total Amount'],
            first_funding_year = None,
        )
        
        # find and add the constituency (do this by name rather than location)
        try:
            constituency_name = row['Constituency']
            if constituency_name in self.constituency_renames:
                constituency_name = self.constituency_renames[constituency_name]
            constituency = self.constituency_qs.get(name=constituency_name)
            data['constituency'] = constituency
        except Place.DoesNotExist:
            self.not_found_constituencies.add( row['Constituency'])
            # warnings.warn("Could not find constituency '%s' on csv line '%u'" % ( row['Constituency'], self.reader.line_num ))
            return None
        
        # Establish the first year that there was funding
        for year in range(2000, 2020):
            key = "%u-%u" % ( year, year+1 )
            amount = re.sub( r'\D', '', row.get(key, '0') )
            if len(amount) and int(amount):
                data['first_funding_year'] = year
                break

        # create the location from coordinates given
        try:
            number_regex = re.compile(r'([-\d\.]+)')
            (lat,lng) = number_regex.findall(row['Loc'])
            point = Point( float(lng), float(lat), srid='4326' )            
            print [ point, point.x, point.y, point.srid ]
            data['location'] = point
        except ValueError:
            # No location found - can't add to database
            return None

        # pprint.pprint( row )
        # pprint.pprint( data )

        # Insert the row into the database
        try:
            project = Project.objects.get(cdf_index=data['cdf_index'])
        except Project.DoesNotExist:
            project = Project()
        
        # Update all fields and save
        is_changed = False
        for key, value in data.items():
            db_val = getattr(project, key) if hasattr(project, key) else None
            if db_val != value:
                setattr(project, key, value)
                is_changed = True
        if is_changed: project.save()



if __name__ == "__main__":
    main()
