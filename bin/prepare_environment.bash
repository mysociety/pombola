#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd "$(dirname $BASH_SOURCE)"/..

# Set DATADIR.
DATADIR=$(grep ^DATA_DIR conf/general.yml | awk '{ print $NF}' | tr -d "'\"")
DATADIR=${DATADIR:-data}

# Some env variables used during development seem to make things break - set
# them back to the defaults which is what they would have on the servers.
PYTHONDONTWRITEBYTECODE=""

virtualenv_dir="${DATADIR}/pombola-virtualenv"
virtualenv_activate="$virtualenv_dir/bin/activate"

# create the virtual environment, install/update required packages
if [ ! -f "$virtualenv_activate" ]
then
    virtualenv $virtualenv_dir
fi

source $virtualenv_activate

# Remove old pip packages installed with the -e switch
rm -rf $virtualenv_dir/src/popit-resolver
rm -rf $virtualenv_dir/src/popit-django
rm -rf $virtualenv_dir/src/pygeocoder
rm -rf $virtualenv_dir/src/za_hansard

# Install all the packages, making sure that a couple of packages that
# used to be required, but which would now cause problems, aren't present:
pip uninstall -y PIL || true
pip uninstall -y South || true
CFLAGS="-O0" pip install -r requirements.txt

# make sure that there is no old code (the .py files may have been git deleted)
find . -name '*.pyc' -delete

# run any pending database migrations
./manage.py migrate

# Install gems in order to compile the CSS
bundle install --deployment --path ${DATADIR}/gems --binstubs ${DATADIR}/gem-bin

# Try to make sure that the MapIt CSS has been generated.
# The '|| echo' means that the script carries on even if this fails,
# since the MapIt CSS isn't essential for the site.
mapit_make_css || echo "Generating MapIt CSS failed"

# gather all the static files in one place
./manage.py collectstatic --noinput

# Generate the down.html from the template, ensures it stay up to date.
./manage.py core_render_template down.html > web/down.default.html
