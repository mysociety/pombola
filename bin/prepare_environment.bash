#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd "$(dirname $BASH_SOURCE)"/..


# Some env variables used during development seem to make things break - set
# them back to the defaults which is what they would have on the servers.
PYTHONDONTWRITEBYTECODE=""


# create the virtual environment, we always want system packages
virtualenv_version="$(virtualenv --version)"
virtualenv_args=""
if [ "$(echo -e '1.7\n'$virtualenv_version | sort -V | head -1)" = '1.7' ]; then
    virtualenv_args="--system-site-packages"
fi
virtualenv $virtualenv_args ../pombola-virtualenv
source ../pombola-virtualenv/bin/activate

# Upgrade pip to a secure version
curl -s https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python

# Install all the packages
pip install Mercurial
pip install -r requirements.txt

# Try to make sure that the MapIt CSS has been generated.
# The '|| echo' means that the script carries on even if this fails,
# since the MapIt CSS isn't essential for the site.
MAPIT_PATH="$(python -c 'import mapit; print mapit.__file__,')"
"$(dirname $MAPIT_PATH)"/../bin/make_css || echo "Generating MapIt CSS failed"

# make sure that there is no old code (the .py files may have been git deleted) 
find . -name '*.pyc' -delete

# get the database up to speed
./manage.py syncdb --noinput
./manage.py migrate

# gather all the static files in one place
./manage.py collectstatic --noinput
