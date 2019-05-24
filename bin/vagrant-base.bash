#!/bin/bash

# Builds base Vagrant box.

## Package Dependencies
DEBIAN_FRONTEND=noninteractive

# Base packages, should really be in an upstream boxen.
apt-get update && apt-get -qq install -y \
    apt-transport-https \
    apt-utils \
    curl \
    dnsutils \
    git \
    locales \
    lockfile-progs \
    lsb-release

# Application dependencies
apt-get -qq install -y \
    libffi-dev \
    libjpeg-dev \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    make \
    openjdk-8-jre-headless \
    postgis \
    postgresql \
    postgresql-9.6-postgis-2.3 \
    python-dev \
    python-gdal \
    python-pip \
    python-virtualenv \
    python-yaml \
    ruby-bundler \
    ruby2.3-dev \
    yui-compressor \
    zlib1g-dev

# Elasticsearch. As we're upgradeing, it might be handy to be able to build various versions.
# Set `ES_VERSION` in the environment to affect this for now.
ES_VERSION=${ES_VERSION:-0.90}

# Import GPG key used to sign repos
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -

# Add appropriate APT repo based on desired version. We're not going higher than 5 for now
# due to a lack of support in the django-haystack package for versions 6 or 7 :(
#
# Earlier versions have key-signing errors in the repos, hence labelling them as trusted.
# ES aren't going to fix these repos for such old versions (see, e.g., https://github.com/elastic/elasticsearch/issues/17724)
case "$ES_VERSION" in
  0.9 | 0.90 | 0.90.13 | 0.90.x )
    echo 'deb [trusted=yes] https://packages.elastic.co/elasticsearch/0.90/debian stable main' > /etc/apt/sources.list.d/elastic-0.90.list
  ;;

  1 | 1.x )
    echo 'deb [trusted=yes] https://packages.elastic.co/elasticsearch/1.7/debian stable main' > /etc/apt/sources.list.d/elasticsearch-1.7.list
  ;;

  2 | 2.x )
    echo 'deb https://packages.elastic.co/elasticsearch/2.x/debian stable main' > /etc/apt/sources.list.d/elasticsearch-2.x.list
  ;;

  5 | 5.x )
    echo 'deb https://artifacts.elastic.co/packages/5.x/apt stable main' > /etc/apt/sources.list.d/elastic-5.x.list
  ;;

  * )
    echo "ERROR: unsupported version of elasticsearch, ${ES_VERSION}"
    exit 1
  ;;
esac

# Install away...
apt-get update && apt-get -qq install elasticsearch -y


# Enable and start elasticsearch
systemctl enable elasticsearch
systemctl start elasticsearch

# Add database role
su -l -c "createuser --createdb --superuser 'vagrant'" postgres
