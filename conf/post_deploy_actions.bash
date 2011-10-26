#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd `dirname $0`/..

# create/update the virtual environment
pip install \
    --enable-site-packages \
    --environment ../mzalendo-virtualenv \
    --requirement requirements.txt \
    --quiet

# use the virtualenv just created/updated
source ../mzalendo-virtualenv/bin/activate

# make sure that there is no old code (the .py files may have been git deleted) 
find . -name '*.pyc' -delete

# go to the project directory for local config
cd pylib/mzalendo

# get the database up to speed
./manage.py syncdb
./manage.py migrate

# gather all the static files in one place
./manage.py collectstatic --noinput

cd --
