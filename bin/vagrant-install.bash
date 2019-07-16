#!/bin/bash

set -e

cd "$(dirname "$0")/.."

COUNTRY_APP=${COUNTRY_APP:-south_africa}
DATADIR=${DATADIR:-data}

DB_NAME="pombola"
REPOSITORY="/vagrant"
LINK_DESTINATION="$HOME/pombola"

ln -sfn "$REPOSITORY" $LINK_DESTINATION

cd "$REPOSITORY"

# Make sure that DATADIR is an absolute path.
if ! [[ $DATADIR =~ ^/ ]] ; then
  DATADIR=${REPOSITORY}/${DATADIR}
fi

echo "Setting up local PATH... "
if ! grep -q 'Set up local PATH for Pombola' $HOME/.bashrc; then
    cat >>$HOME/.bashrc <<EOBRC
# Set up local PATH for Pombola
export PATH="${DATADIR}/gem-bin:\$PATH"
EOBRC
fi

if [ ! -f conf/general.yml ]; then
  echo -n "Setting up conf/general*.yml files and media_root directories... "
  RANDOM_STRING=$(< /dev/urandom tr -dc A-Za-z0-9 | head -c32)
  sed -r \
    -e "s,^( *POMBOLA_DB_HOST:).*,\\1 ''," \
    -e "s,^( *POMBOLA_DB_NAME:).*,\\1 '$DB_NAME'," \
    -e "s,^( *POMBOLA_DB_USER:).*,\\1 'vagrant'," \
    -e "s,^( *DATA_DIR:).*,\\1 '$DATADIR'," \
    -e "s,^( *COUNTRY_APP:).*,\\1 '$COUNTRY_APP'," \
    -e "s,^( *DJANGO_SECRET_KEY:).*,\\1 '$RANDOM_STRING'," \
    conf/general.yml-example > conf/general.yml
fi

mkdir -p ${DATADIR}/media_root

if ! psql -l | egrep "^ *$DB_NAME *\|" > /dev/null; then
  createdb --owner "vagrant" "$DB_NAME"
  echo 'CREATE EXTENSION postgis; CREATE EXTENSION postgis_topology' | psql "$DB_NAME"
  psql "$DB_NAME" < /usr/share/postgresql/9.6/contrib/postgis-2.3/legacy_minimal.sql
fi

bin/prepare_environment.bash

# Load data
case "$COUNTRY_APP" in
  south_africa )
    LIVE_URL='https://www.pa.org.za'
  ;;
  * )
    echo "Unknown country, ${COUNTRY_APP}"
    LIVE_URL=
  ;;
esac

if [ -n "$LIVE_URL" ]; then
  echo "Downloading and loading database dump for ${COUNTRY_APP}..."
  TMP_SCHEMA=$(mktemp /var/tmp/schema.XXXXX)
  TMP_DATA=$(mktemp /var/tmp/data.XXXXX)
  curl -s -S -o ${TMP_SCHEMA} ${LIVE_URL}/media_root/dumps/pg-dump_schema.sql.gz
  curl -s -S -o ${TMP_DATA} ${LIVE_URL}/media_root/dumps/pg-dump_data.sql.gz
  gunzip -c ${TMP_SCHEMA} | psql ${DB_NAME}
  gunzip -c ${TMP_DATA} | psql ${DB_NAME}
  rm $TMP_DATA
  rm $TMP_SCHEMA
else
  echo "Skipping live database import."
fi

# Set up virtualenv activation on login
if ! grep -q 'Set up virtualenv activation for Pombola' $HOME/.bashrc; then
    cat >>$HOME/.bashrc <<EOBRC

# Set up virtualenv activation for Pombola
source "${DATADIR}/pombola-virtualenv/bin/activate"
EOBRC
fi

echo "==> Installation done!"
echo "==> To view, first log in and run /vagrant/manage.py runserver 0.0.0.0:8000"
echo "==> Then visit http://localhost:8000 in your browser."
echo
