import re 
import csv
import sys

from optparse import make_option

from django.core.management.base import LabelCommand
from django.contrib.gis.geos import Point

from mapit.models import Area, Generation, Type, NameType, Country

class Command(LabelCommand):
    """Read a file in, extract coordinates and lookup the constituency.
    
    Outputs the coordinates, constituency slug and name as CSV to STDOUT
    
    input is one pair of coords per line, eg:
    
    (1.23, 4.56)
    
    """

    help = 'Import KML data'
    args = '<KML files>'

    writer = csv.writer(sys.stdout)

    def handle_label(self, input_coords, **options):

        with open(input_coords) as input_file:
            for line in input_file.readlines():
                self.process_line( line.strip() )
                
                


    def process_line(self, raw_line):
        """Extract coords from line and output constituency found"""
        
        # print raw_line
        line = re.sub(r'[^\d.,\-]+', '', raw_line)

        # The lat, lng here might be the wrong way round :)
        lng, lat = map( lambda x: float(x), re.split(',', line) )
        point = Point( lat, lng, srid=4326)

        # print point
        
        areas = Area.objects.by_location( point )
        
        output = [ raw_line ]

        if areas:
            places = areas[0].place_set.all()
            if places:
                place = places[0]            
                output.append( place.name )
                output.append( place.slug )

        self.writer.writerow( output )
