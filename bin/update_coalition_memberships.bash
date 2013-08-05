#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd `dirname $0`/../mzalendo

source ../../pombola-virtualenv/bin/activate

./manage.py kenya_assign_aspirants_to_coalitions
