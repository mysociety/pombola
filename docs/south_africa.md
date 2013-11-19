# Setting up South Africa pombola data

## Map data

Firstly, download the boundary files from
http://www.demarcation.org.za/Downloads/Boundary/Boundaries.html and unrar
them.

To set up MapIt with these boundaries, you need to create a new MapIt
generation, load in the South Africa fixture, load in the boundaries, then
activate the generation. Hopefully something like this:

    $ python manage.py mapit_generation_create --desc "Initial import" --commit
    $ python manage.py loaddata mapit_south_africa
    $ python manage.py south_africa_import_boundaries --wards=pombola/south_africa/boundary-data/Wards2011.shp --districts=pombola/south_africa/boundary-data/DistrictMunicipalities2011.shp --provinces=pombola/south_africa/boundary-data/Province_New_SANeighbours.shp --locals=pombola/south_africa/boundary-data/LocalMunicipalities2011.shp --commit
    $ python manage.py mapit_generation_activate --commit

## People and organisation data

Then, to load in some people and organisation data:

    $ python manage.py core_import_popolo pombola/south_africa/data/south-africa-popolo.json  --commit

Run the command to clean up imported slugs:

    $ python manage.py core_list_malformed_slugs --correct

To load in constituency offices, download a CSV from the below, and run the following.
https://docs.google.com/spreadsheet/ccc?key=0Am9Hd8ELMkEsdHpOUjBvNVRzYlN4alRORklDajZwQlE.
If you run into any issues with this you might need to remove the
geocode cache at `pombola/south_africa/management/commands/.geocode-request-cache`.

    $ python manage.py south_africa_import_constituency_offices --commit --verbose <file.csv>

## Hansard, Committee and Question data

First, initialise the resolver 

    $ python manage.py  popit_resolver_init --popit-api-url=http://za-peoples-assembly.popit.mysociety.org/api/v0.1

This will load data from popit (an instance with the same data used to populate
the pombola person DB above!) and initialise the Elasticsearch index.

### Just load some sample data:

To load in some example SayIt data, fetch the speeches/fixtures/test_inputs/

    $ python manage.py load_akomantoso --dir <speeches/fixtures/test_inputs/> --commit

### Or run complete parse 

This may be called from command line, or added to cron to run regularly

    $ bin/update_hansard.bash
