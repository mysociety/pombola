#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd `dirname $0`/..

# Get application config
source commonlib/shlib/deployfns
read_conf conf/general.yml

# Activate virtualenv
virtualenv_dir="${OPTION_DATA_DIR}/pombola-virtualenv"
source ${virtualenv_dir}/bin/activate

./manage.py hansard_check_for_new_sources
./manage.py hansard_process_sources
./manage.py hansard_assign_speakers
