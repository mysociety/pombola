# Importing PUN data

This is a guide to the steps required to add the PUN data to the database.

It is complicated as the names used for the LGAs are duplicated and some appear
in several states. The original import of boundaries assumed that this could
not be the case and so only a single entry was created (I think, it was a while
back).

## Helper script

There is a script `name_helper.py` that you can run several times to correctly
set up the names. The following steps all require running the script, it will
not let you proceed until the previous step has been completed.

## Check that all the state names are correct.

There are a couple of states that do not have matching names. Use the admin to
find them and then create an alternative name.

## Deal with the duplicated LGAs

This is a mostly manual step. The code will list all the LGAs that have
duplicated names and that cannot be exactly matched to an LGA area (including
matching the parent to the state).

Fix this by hand in the admin (including possibly using `./manage.py dbshell`
to set the `name` field which is not done via admin).
