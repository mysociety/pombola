#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd `dirname $0`/..

# Set DATADIR.
DATADIR=$(grep ^DATA_DIR conf/general.yml | awk '{ print $NF}' | tr -d "'\"")
DATADIR=${DATADIR:-data}

# Activate virtualenv
virtualenv_dir="${DATADIR}/pombola-virtualenv"
source ${virtualenv_dir}/bin/activate

./manage.py hansard_check_for_new_sources
./manage.py hansard_process_sources
./manage.py hansard_assign_speakers
