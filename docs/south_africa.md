# Setting up South Africa pombola data

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

Then, to load in some people and organisation data:

    $ python manage.py core_import_popolo pombola/south_africa/data/sa.json  --commit

To load in some example SayIt data, fetch the speeches/fixtures/test_inputs/

    $ python manage.py load_akomantoso --dir <speeches/fixtures/test_inputs/> --commit

