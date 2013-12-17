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
matching the parent to the state). It will not proceed if there are any.

Fix this by hand in the admin (including possibly using `./manage.py dbshell`
to set the `name` field which is not done via admin).

```
Set parent of existing Ifelodun (554) to Osun (31)
Create new Ifelodun with parent Kwara (25)
update mapit_area set name = 'Ifelodun' where name = '';

existing Nasarawa (594) gets parent Nassarawa (27)
new Nasarawa gets parent KANO (21)
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

