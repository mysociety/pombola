#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd `dirname $0`/..

./bin/run_management_command popit_resolver_init --popit-api-url=http://za-new-import.popit.mysociety.org/api/v0.1/

./bin/run_management_command za_hansard_check_for_new_sources
./bin/run_management_command za_hansard_run_parsing
./bin/run_management_command za_hansard_load_into_sayit

# Run the ZA Hansard questions importer (all steps)
./bin/run_management_command za_hansard_q_and_a_scraper --run-all-steps

# Run the committee minutes scraper and imports
./bin/run_management_command za_hansard_pmg_api_scraper --scrape --save-json --import-to-sayit --commit
