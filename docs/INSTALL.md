# Install

Pombola is mostly a standard Django project. There are some unusual dependencies that are noted below.

## Where to put the code

In addition to the downloaded code several other directories are needed for
dynamic data such as the search indexes, uploaded images, various caches etc.

These extra directories are by default put inside the `data/` directory, although
this can be modified using the `DATA_DIR` configuration variable.

## Getting the code

The code is available via github: https://github.com/mysociety/pombola

```
git clone https://github.com/mysociety/pombola.git
```

## Vagrant

The `Vagrantfile` will set up the South African site by default. You can
override this by setting `COUNTRY_APP` in the environment, e.g.:
```
COUNTRY_APP=kenya vagrant up
```
Or by creating/updating to relevant variable in `conf/general.yml`
manually (otherwise this will be created the first time you run
`vagrant up`).

The provisioning script will download the public database dumps from
the live site for the appropriate country and import this into the
local database.

It doesn't attempt to get all uploaded media, like images of
politicians, however, so if you want them you should rsync them yourself.

It is also possible to control the version of Elasticsearch installed
in the Vagrant box using the `ES_VERSION` environment variable. The
project uses the `django-haystack` package and this currently supports
ES versions up to 5, so you can install 0.90, 1, 2 or 5.
```
ES_VERSION=5 vagrant up
```

## Manual installation

### Non-python dependencies

There are some dependencies that need to be installed. Please see the `conf/packages` file for details.

### Databases

A Postgis enabled Postgres database is required

Create the database and enable the Postgis extensions - assuming here that you're calling it 'pombola'

```
createdb pombola
echo 'CREATE EXTENSION postgis; CREATE EXTENSION postgis_topology' | psql pombola
```

### Configuration files

Do to the pombola Django project:

```
cd pombola
```

Copy config example and set values needed

```
cp conf/general.yml-example conf/general.yml
nano conf/general.yml
```

### Python dependencies and database setup

Most of this is done using the `bin/prepare_environment.bash` script. This will create the virtual environment, install needed python dependencies and
then set up the database:

```
bin/prepare_environment.bash
```

If this step fails, please consult [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

### Virtualenv

Now that the environment has been created you need to enable it:
```
source data/pombola-virtualenv/bin/activate
```

## Start the dev server

The dev server will allow you to check that everything is working as expected.

```
./manage.py runserver
```

If you are running this inside a Vagrant box, you'll need to bind to all
interfaces:

```
./manage.py runserver 0.0.0.0:8000
```
