#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd `dirname $0`/../mzalendo

source ../../mzalendo-virtualenv/bin/activate

./manage.py scorecard_update_person_contact_scores

