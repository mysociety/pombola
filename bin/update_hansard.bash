#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd `dirname $0`/..

source ../pombola-virtualenv/bin/activate

./manage.py hansard_check_for_new_sources
./manage.py hansard_process_sources
./manage.py hansard_assign_speakers
