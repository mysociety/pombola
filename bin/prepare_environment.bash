#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd "$(dirname $BASH_SOURCE)"/..


# Some env variables used during development seem to make things break - set
# them back to the defaults which is what they would have on the servers.
PYTHONDONTWRITEBYTECODE=""

# create the virtual environment, install/update required packages
virtualenv ../mzalendo-virtualenv
source ../mzalendo-virtualenv/bin/activate
pip install Mercurial

# We replaced PIL with Pillow, but "pip install -r" won't remove PIL
# just because it has disappeared from the requirements.txt file.  If
# we're at this version of the source code, however, we definitely
# want Pillow in preference to PIL, so just remove the latter:
pip uninstall -y PIL || true

pip install -r requirements.txt

# make sure that there is no old code (the .py files may have been git deleted) 
find . -name '*.pyc' -delete

# go to the project directory for local config
cd mzalendo

# get the database up to speed
./manage.py syncdb --noinput
./manage.py migrate

# gather all the static files in one place
./manage.py collectstatic --noinput
