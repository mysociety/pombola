#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd `dirname $0`/../pombola

source ../../pombola-virtualenv/bin/activate

./manage.py scorecard_update_person_contact_scores

