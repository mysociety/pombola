#!/bin/sh

PARENT_SCRIPT_URL=https://github.com/mysociety/commonlib/blob/master/bin/install-site.sh

misuse() {
  echo The variable $1 was not defined, and it should be.
  echo This script should not be run directly - instead, please run:
  echo   $PARENT_SCRIPT_URL
  exit 1
}

# Strictly speaking we don't need to check all of these, but it might
# catch some errors made when changing install-site.sh

[ -z "$DIRECTORY" ] && misuse DIRECTORY
[ -z "$UNIX_USER" ] && misuse UNIX_USER
[ -z "$REPOSITORY" ] && misuse REPOSITORY
[ -z "$REPOSITORY_URL" ] && misuse REPOSITORY_URL
[ -z "$BRANCH" ] && misuse BRANCH
[ -z "$SITE" ] && misuse SITE
[ -z "$DEFAULT_SERVER" ] && misuse DEFAULT_SERVER
[ -z "$HOST" ] && misuse HOST
[ -z "$DISTRIBUTION" ] && misuse DISTRIBUTION
[ -z "$DISTVERSION" ] && misuse DISTVERSION
[ -z "$DEVELOPMENT_INSTALL" ] && misuse DEVELOPMENT_INSTALL

if [ ! "$DEVELOPMENT_INSTALL" = true ]; then
    apt-get install -qq -y python-flup gunicorn
    install_nginx
    add_website_to_nginx
fi

# XXX packages file e.g. asks for Apache and central script doesn't
# like comments or alternatives at present
#install_website_packages
apt-get install -y -qq make postgresql postgis postgresql-9.3-postgis-2.1 libpq-dev python-gdal python-dev python-pip python-virtualenv libxml2-dev libxslt1-dev openjdk-7-jre-headless libjpeg-dev yui-compressor libffi-dev ruby1.9.1-dev ruby-bundler >/dev/null

if ! dpkg -l elasticsearch 2>/dev/null | grep -q ^.i; then
    echo "Installing elasticsearch..."
    curl -s -O https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-0.90.3.deb
    dpkg -i elasticsearch-0.90.3.deb
    echo $DONE_MSG
fi

install_postgis

if [ x"$DISTRIBUTION" = x"ubuntu" ] && [ x"$DISTVERSION" = x"trusty" ]
then
    # On trusty, the database user will need to be a superuser so that
    # it can create the PostGIS extension; we'll drop that privilege
    # afterwards:
    add_postgresql_user --superuser
else
    add_postgresql_user
fi

su -l -c "$REPOSITORY/bin/install-as-user '$UNIX_USER' '$HOST' '$DIRECTORY' '$DEVELOPMENT_INSTALL'" "$UNIX_USER"

if [ x"$DISTRIBUTION" = x"ubuntu" ] && [ x"$DISTVERSION" = x"trusty" ]
then
    sudo -u postgres psql -c "ALTER USER $UNIX_USER WITH NOSUPERUSER"
fi

if [ ! "$DEVELOPMENT_INSTALL" = true ]; then
    install_sysvinit_script
    echo Installation complete - you should now be able to view the site at:
    echo   http://$HOST/
    echo Or you can run the tests by switching to the "'$UNIX_USER'" user and
    echo running something like: $REPOSITORY/manage.py test
fi
