#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd `dirname $0`/../mzalendo

source ../../mzalendo-virtualenv/bin/activate

./manage.py hansard_check_for_new_sources
./manage.py hansard_process_sources
./manage.py hansard_assign_speakers

# This will print out to STDOUT if it finds any. This should then get emailed to
# the right people by the cron script.
./manage.py hansard_list_unmatched_speakers
