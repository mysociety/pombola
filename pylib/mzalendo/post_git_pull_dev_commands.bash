#!/bin/bash

set -e

MZALENDO_DIR="$( cd "$( dirname "$0" )/../.." && pwd )"
DJANGO_PROJECT_DIR="$( cd "$( dirname "$0" )" && pwd )"

# echo "MZALENDO_DIR: $MZALENDO_DIR"
# echo "DJANGO_PROJECT_DIR: $DJANGO_PROJECT_DIR"

# bring the git repo up to speed
cd $MZALENDO_DIR
git submodule init
git submodule update
git submodule

# do the django bits
cd $DJANGO_PROJECT_DIR

# bring the database up to speed
./manage.py syncdb
./manage.py migrate

# rebuild the index
./manage.py rebuild_index --noinput

