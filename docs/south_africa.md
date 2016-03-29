# Setting up South Africa pombola data

The easiest way to import the data for People's Assembly is to
use the public PostgreSQL database dumps.  You can download gzip
compressed dumps of the
[schema](http://www.pa.org.za/media_root/dumps/pg-dump_schema.sql.gz)
and the
[data](http://www.pa.org.za/media_root/dumps/pg-dump_data.sql.gz).

You should import them into a new PostGIS database with:

    gunzip -c pg-dump_schema.sql.gz pg-dump_data.sql.gz | psql <DB-NAME>

... where `<DB-NAME>` is the database name.

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

#### Reparsing hansard

It's possible to do a full reparse of the hansards using the following commands.
Please note that this will delete any existing sources and re-fetch them, though
this is probably what you want as the sources might have been updated with
spelling/grammar corrections. Also be aware that the
`za_hansard_load_into_sayit` command with the `--delete-existing` flag will
delete existing speeches that have been tagged as 'hansard', and will therefore
break the permalinks to individual speeches.

**WARNING: This is destructive and will take several hours to complete.**

    $ python manage.py popolo_name_resolver_init
    $ python manage.py za_hansard_check_for_new_sources --check-all --delete-existing
    $ python manage.py za_hansard_run_parsing
    $ python manage.py za_hansard_load_into_sayit --delete-existing

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


