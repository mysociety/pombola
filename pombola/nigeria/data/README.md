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

Run it as:

    ./name_helper.py polling_unit_wards.csv

This script is not efficient, but quite effective :)

### Check that all the state names are correct.

There are a couple of states that do not have matching names. Use the admin to
find them and then create an alternative name.

### Deal with the duplicated LGAs

This is a mostly manual step. The code will list all the LGAs that have
duplicated names and that cannot be exactly matched to an LGA area (including
matching the parent to the state). It will not proceed if there are any.

Fix this by hand in the admin (including possibly using `./manage.py dbshell`
to set the `name` field which is not done via admin).

```
Set parent of existing Ifelodun (554) to Osun (31)
Create new Ifelodun with parent Kwara (25)
update mapit_area set name = 'Ifelodun' where name = '';

existing Nasarawa (594) gets parent Nassarawa (27)
existing Nassarawa gets parent KANO (21)
update mapit_area set name = 'Nasarawa' where name = '';

existing BASSA (40) gets parent Plateau (33)
new BASSA gets parent Kogi (24)
update mapit_area set name = 'BASSA' where name = '';

existing OBI (215) gets parent Nasarawa (27)
new OBI gets parent BENUE (8)
update mapit_area set name = 'OBI' where name = '';

existing IREPODUN (558) in Osun (31)
new IREPODUN in Kwara (25)
update mapit_area set name = 'IREPODUN' where name = '';

existing SURULERE (585) is in Oyo (32)
new SURULERE in LAGOS (26)
update mapit_area set name = 'SURULERE' where name = '';
```

### Match up non-exact matches

The script will now go through all the LGA entries that it cannot get an exact
match for and suggest suitable matches. Select them using the number assigned.
If no sure just let it go, and it will come around again later. The search is
not terribly elegant so at the end all available matches will be listed.

Each time you select an option a `names` entry is created.

This continues until all LGAs are matched.

Some less obvious matches:

    'KOGI K. K.' is 'Kotonkar'

If at the end there are still unmatched areas use the admin to sort them out
(deleting mischosen names and rerunning script works well).

## Import the DUN codes and create the wards

There is a second script that can be used once `name_helper.py` is happy. Run
it as:

    ./add_polling_units_to_mapit.py polling_unit_wards.csv


