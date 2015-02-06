# Changing the IDs used by PopIt

Sometimes it may be necessary to change the format of the IDs
used in PopIt, and this has an effect on the name matching in
PopIt.  If you need to do this, here are the steps that are
required to make sure everything still works.  (Obviously try
this on a development version or staging Pombola / staging PopIt
to make sure it works as expected first.)

* Change the way that PopIt IDs are formed in the
  `get_popolo_id` method of `pombola/core/models.py`

* Generate a new dump of the Pombola database with:

```
mkdir ~/pombola-dump
./manage.py core_export_to_popolo_json ~/pombola-dump/ http://www.pa.org.za
```

* Replace the PopIt database with a command like the
  following. (Make very sure that you know what NODE_ENV should
  be set to, what the PopIt instance slug is, and what the PopIt
  master database is, or you may end up replacing the wrong
  database entirely.)

```
cd ~/popit/popit/
NODE_ENV=development bin/replace-database ~/pombola-dump/mongo- south-africa popitdev__master
```

* Restart PopIt, as that command suggests

* Add django-popit Person objects for each of these PopIt
  people with new IDs and replace all EntityNames (used for
  indexing in Elasticsearch for name resolution) with new ones
  pointing to those django-popit Person objects with:

```
./manage.py popit_resolver_init
```

Note that at this stage, appearances should still be appearing
on each politician's page - during the next steps, there will be
a period where they disappear. (Between the SayIt speakers being
updated and the code that knows where to find the speakers being
deployed.)

* Now you have to change the script
  `pombola/core/management/commands/core_fix_sayit_speakers.py`
  such that `current_popit_id_re` only matches the new ID scheme
  and `other_popit_id_re` also matches the previous ID scheme.

* Now run that script to apply those changes

```
./manage.py core_fix_sayit_speakers
```

* Change `expected_popit_id` in `pombola/core/views.py` to match
  the new ID scheme.

* Change the match on `popit_id` in the
  `SASpeakerRedirectView.get_redirect_url` method in
  `pombola/south_africa/views.py` to match the new ID.
