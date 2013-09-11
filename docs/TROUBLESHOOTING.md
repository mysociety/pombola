# TROUBLESHOOTING

If something goes wrong please check the following for help.
If your problem is not listed please add it after fixing.

## Remember to set up the environment!

If you see errors like this...

    File "./manage.py", line 5, in <module>
    import settings
    ImportError: No module named yaml

...then you probably forgot to set the virtualenv for your current session.
See the VIRTUALENV section in INSTALL.txt.


## Remember to install all required modules

If you see errors like this...

    Error: No module named XXXX

...then you might need to make sure your modules are up to date. Run:

    pip install -r ../requirements.txt

...to get all the modules that Pombola needs. This may be necessary
ifyou have updated your Pombola by pulling from the git repository
since your initial installation and the requirements have changed.


## Run migrations after an update that has changed the db schema

If you see error like this...

    DatabaseError while rendering: column XXX does not exist

...then you may need to run a database migration. Run:

    ./manage.py migrate

...to make sure your database is up-to-date with your current installation. This may
be necessary if you have updated your Pombola by pulling from the git repository
since your initial installation. It's safe to run even if there have been no changes.


## ./manage.py migrate will not run correctly

Check that the database has PostGIS added to it


## Web requests block

If location searches black then check that the external requests to Google are
not hanging.


## Location searches return old/bad data

Try deleting the cached search in `httplib2_cache`


## Caching does not appear to be working

Point your browser at `/status/memcached/` - first hit should save a val to
cache and subsequent ones should show that it is in the cache until the ttl
expires.

Check that you are not logged in, and don't have a sessionid or csrf_token
cookie - both of which will cause caches to fetch you new content.


## No featured people on the home page: just a big Pombola logo

The home page displays a random featured person (typically an MP) provided there is at least
one in the database with can_be_featured set to true. To choose people to feature, log into
the admin and choose people from Core > Persons. Select the individuals you want to feature
by the checkbox "can be featured" for each one.

## Running ../bin/prepare_environment.bash fails when building GDAL

Installation of the Python bindings for GDAL can be difficult,
and working out what the easiest solution for you is will depend
on your version of virtualenv, what the version of your system's
GDAL library is, what operating system you're using, and so on.

Assuming that you're using Debian-based distribution of
GNU/Linux there are broadly two routes to making this work:

### Use your system's python-gdal package

The first option is to set up your pombola virtualenv to allow
system Python packages to be used, and install your
distribution's python-gdal package.  To make sure that that
package is installed, run:

    sudo apt-get install python-gdal

Now you need to make sure you can import that package when your
virtualenv is activated.  Whether the virtualenv created by
prepare_environment.bash is using your system Python packages
depends on the version of virtualenv on your system,
unfortunately.  To test this, run:

    find pombola-virtualenv -name no-global-site-packages.txt

If no file is found, then the system packages are accessible,
and you should be able to rerun prepare_environment.bash without
problems.

If that file is found, then you have a recent version of
virtualenv, and you should edit prepare_environment.bash
to change the line:

    virtualenv ../pombola-virtualenv

... to:

    virtualenv --system-site-packages ../pombola-virtualenv

If you then rerun prepare_environment.bash, everything should be
fine - pip will find that the system python-gdal installation
satisfies the GDAL requirement.

### Fix the build of the GDAL bindings in your virtualenv

The other option is to fix the build of the Python GDAL bindings
in your virtualenv.  Firstly, make sure that you have the
GDAL development library installed, with:

    sudo apt-get install libgdal1-dev

Then rerun prepare_environment.bash.  If you get a compilation
error, then you'll find that the source tree and partial build
is left in pombola-virtualenv/build/GDAL.  To work on fixing
this, make sure that you first activate the virtualenv in your
current shell:

    source pombola-virtualenv/bin/activate

Some build problems can arise from a mismatch between the
version of the Python GDAL bindings that is used by pip by
default (currently that's 1.9.1) and the version of the
development library you have on your system.  For example, on
the system I'm testing on, this command shows that I'm using
1.7.3:

    dpkg --status libgdal1-dev

That version is incompatible with 1.9.1, and will produce the
error `‘VSILFILE’ has not been declared` when building GDAL,
even if you've fixed the other problems below.

From the listing at http://pypi.python.org/simple/GDAL/ I can
see that the closest available version is 1.7.1, so I'm going to
retry installing that version.  First, remove the old partial
installation:

    rm -r pombola-virtualenv/build/GDAL

And try to install the specific version we want:

    pip install GDAL==1.7.1

If that works, you can return prepare_environment.bash, and
you should be done.  If you get the following error:

    extensions/gdal_wrap.cpp:2813:22: fatal error: cpl_port.h: No such file or directory

Then try the following steps:

    export CFLAGS="$(gdal-config --cflags)"
    pip install --no-download GDAL==1.7.1

If you then get the following error:

    /usr/bin/ld: cannot find -lgdal

Then look at the output of:

    gdal-config --libs

For example, in my test case that is:

    -L/usr/lib -lgdal1.7.0

So I should edit `pombola-virtualenv/build/GDAL/setup.py` and
change the line:

    libraries = ['gdal']

... to:

    libraries = ['gdal1.7.0']

Then, do the following steps:

    export LDFLAGS="$(gdal-config --libs)"
    pip install --no-download GDAL==1.7.1

The build should then succeed, and if you rerun
prepare_environment.bash then the installation should complete
successfully.
