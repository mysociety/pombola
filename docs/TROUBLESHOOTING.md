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


## You need to merge two people together

There is a management command `core_merge_people` that can do this for you.

