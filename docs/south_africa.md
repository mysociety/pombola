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

    $ python manage.py core_import_popolo pombola/south_africa/data/south-africa-popolo.json  --commit

Run the command to clean up imported slugs:

    $ python manage.py core_list_malformed_slugs --correct

To load in constituency offices, download a CSV from the below, and run the following.
https://docs.google.com/spreadsheet/ccc?key=0Am9Hd8ELMkEsdHpOUjBvNVRzYlN4alRORklDajZwQlE.
If you run into any issues with this you might need to remove the
geocode cache at `pombola/south_africa/management/commands/.geocode-request-cache`.

    $ python manage.py south_africa_import_constituency_offices --commit --verbose <file.csv>

To load in some example SayIt data, fetch the speeches/fixtures/test_inputs/

    $ python manage.py load_akomantoso --dir <speeches/fixtures/test_inputs/> --commit

Places can be created to match all those in the mapit database.

    $ ./manage.py core_create_places_from_mapit_entries PRV
    $ ./manage.py core_create_places_from_mapit_entries DMN
    $ ./manage.py core_create_places_from_mapit_entries LMN
    $ ./manage.py core_create_places_from_mapit_entries WRD

Once created they can then be structured into a hierarchy.

    $ ./manage.py core_set_area_parents wards:local-municipality
    $ ./manage.py core_set_area_parents local-municipality:district-municipality
    $ ./manage.py core_set_area_parents district-municipality:province

Currently the data for the metropolitan municipalites is in a funny place - see
https://github.com/mysociety/pombola/issues/695. Once fixed though these
commands should add the data for them:

    !!TODO!! ./manage.py core_create_places_from_mapit_entries MMN
    !!TODO!! ./manage.py core_set_area_parents wards:metropolitan-municipality
    !!TODO!! ./manage.py core_set_area_parents metropolitan-municipality:province

Load in the Members' Interests data (if there are already some entries you should delete them all usig nthe admin):

    $ ./manage.py interests_register_import_from_json pombola/south_africa/data/members-interests/2010_for_import.json
    $ ./manage.py interests_register_import_from_json pombola/south_africa/data/members-interests/2011_for_import.json
    $ ./manage.py interests_register_import_from_json pombola/south_africa/data/members-interests/2012_for_import.json
    $ ./manage.py interests_register_import_from_json pombola/south_africa/data/members-interests/2013_for_import.json

## Updating parliamentary appearances content (Hansard, Committee Minutes, Questions)

We get content from various locations through scripts which live in the za-hansard project (to be included as
an optional app, as documented in general.yml-example).

The script `bin/update_za_hansard.bash` should be run from cron (e.g. set in
`conf/crontab.ugly` for mySociety installs) and can also be run manually.  

However it may be useful to run individual components, to be able to debug
errors.  The steps run in the `update_za_hansard.bash` are documented here in
more detail:

### Hansards

There are three management commands to be run for Hansard content. 

    # First, scrape the web-pages of parliament to find new "source" records, and metadata.
    # By default we start from the most recent document, and then scrape backwards in time,
    # stopping when we see the first document we have already spotted before.

    $ python manage.py za_hansard_check_for_new_sources
        --check-all    (e.g. do not stop on seen)
        --start-offset 
        --limit

    # Then we run the parser:

    $ python manage.py za_hansard_run_parsing
        --id              (parse just a given id)
        --retry           (retry failed parses)
        --retry-download  (retry failed downloads, e.g. 404)
        --redo            (redo all, including completed ones)
        --limit

    # Finally, we import into SayIt

    $ python manage.py za_hansard_load_into_sayit
        --id              (import just a given id)
        --instance        (only needed if you have renamed the sayit instance from Default)
        --limit

Note that though we have a --redo option for the parsing, the sayit import will not run again
if the database record for the za_hansard Source already has a `sayit_section_id`.

As the import will always create a new section and speeches, this could lead to
URLs changing.  Bearing this in mind, and with appropriate care, it is possible
to (manually) null the appropriate sayit_section_id, delete the sayit sections/speeches,
and then rerun the import.

## Committee Minutes

This script runs against the PMG website, and was originally supplied by Geoff Kilpin who is
working with them.  It is presented as a single management command, with a
number of steps, which can be run together as:

    $ python manage.py za_hansard_pmg_scraper --scrape --save-json --import-to-sayit

You can alternatively run those steps separately

        --scrape 
        --save-json 
        --import-to-sayit

Other flags are:

        --scrape-with-json   (appears to be mostly for debugging, not otherwise used)

        --limit
        --fetch-to-limit  (works like --check-all for Hansard)

        --retries         (as the PMG server is currently overloaded, we have a default max-retries of 3)

    # For --import-to-sayit action
        --instance           not required unless you have renamed the sayit instance from 'default'
        --delete-existing    will *delete* existing sayit sections, and reimport them

## Question Scraper

This script runs against the Parliament website, and was originally supplied by
Geoff Kilpin from PMG.  Again, it is presented as a single management command,
with a number of steps, which can be run together as:

    $ python manage.py za_hansard_q_and_a_scraper --run-all-steps

Or you can run individual steps as follows:

    $ python manage.py za_hansard_q_and_a_scraper 
        --scrape-questions  # step 1
        --scrape-answers    # step 2
        --process-answers   # step 3
        --match-answers     # step 4
        --save              # step 5 (as JSON)
        --import-into-sayit # step 6

Yes, that is quite a lot of steps.  (NB: check Duncan's work on refactoring Q/A
parser, in case it affects any of these steps.)

Other flags are:

        --instance
        --limit
        --fetch-to-limit  (works like --check-all for Hansard)


