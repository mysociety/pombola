# from optparse import make_option
# from pprint import pprint
import csv
import StringIO
# import re
# 
from django.core.management.base import BaseCommand
from django.conf import settings

from mzalendo.core import models

class Command(BaseCommand):
    help = """
        Output CSV of all constituencies and their current political affiliation.
        Suitable for loading in to a Google Fusion Table to produce a map,
    """

    def handle(self, **options):

        # from http://colorbrewer2.org/index.php?type=diverging&scheme=Spectral&n=11
        party_to_colour = {
            'Party of National Unity': '#9e0142',
            'Kenya African National Union': '#d53e4f',
            'Orange Democratic Movement': '#f46d43',
            'Orange Democratic Movement Party Of Kenya': '#fdae61',
            'NARC - Kenya': '#fee08b',
            'Safina Party Of Kenya': '#ffffbf',
            'National Rainbow Coalition': '#e6f598',
            'Ford People': '#abdda4',
            'Democratic Party': '#66c2a5',
            'spare': '#3288bd', # not used
            'other': '#5e4fa2', 
        }

        rows       = []
        fieldnames = ['name', 'person', 'party', 'color', 'location']
        

        # get all the constituencies
        constituencies = models.Place.objects.all().filter(kind__slug='constituency');

        for con in constituencies:
            row = {
                'name':     con.name,
                'person':   '',   
                'party':    '',
                'location': '',
                'color':    '',
            }

            # get the person and party data
            pos = con.current_politician_position()
            if pos:
                if pos.person:
                    person = pos.person
                    row['person'] = person.name;
                    
                    parties = []
                    for party in person.parties():
                        parties.append( party.name)
                    row['party'] = ', '.join(parties)
            
                    row['color'] = party_to_colour.get( row['party'] ) or party_to_colour['other'];
            
            # get the kml positions
            area = con.mapit_area
            if area:
                all_areas = area.polygons.all()

                if len(all_areas) > 1:
                    all_areas = all_areas.collect()
                elif len(all_areas) == 1:
                    all_areas = all_areas[0].polygon
                # else:
                #     return output_json({ 'error': 'No polygons found' }, code=404)

                # apply a simplify_tolerance to make CSV smaller
                all_areas = all_areas.simplify(0.001)                                        

                row['location'] = all_areas.kml
                        
            rows.append(row)


        csv_output = StringIO.StringIO()
        writer = csv.DictWriter( csv_output, fieldnames )

        fieldname_dict = {}
        for key in fieldnames:
            fieldname_dict[key] = key
        writer.writerow( fieldname_dict )
        
        for data in rows:
            writer.writerow( data )
        
        print csv_output.getvalue()
