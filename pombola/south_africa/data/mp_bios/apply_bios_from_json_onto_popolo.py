import json
import re
import sys

# # Expected JSON is an array of entries:
# #
# # [
# #     {
# #         "name": "John Smith",
# #         "bio": "Blah blah"
# #     },
# #     ....
# # ]
# #
# # ``name`` should match the Person's ``legal_name`` and ``bio`` is stored in their summary field.

# Open the two JSON files - one for the popolo and the other the summaries to
# add. Presumes that the CWD is the south_africa/data dir
popolo_data = json.loads( open( 'south-africa-popolo.json' ).read() )
bio_data    = json.loads( open( 'mp_bios/mpbios.json'      ).read() )


# change the bio data so that it is a lookup hash based on name
bio_lookup = {}
for entry in bio_data:
    bio_lookup[entry['name']] = entry['bio']


# Go through all people in popolo and add bio data to them, deleting as done
for person in popolo_data['persons']:
    name = person['name']
    if name not in bio_lookup: continue

    person['biography'] = bio_lookup[ name ]
    del bio_lookup[name]


# Warn if there are any entries that have not been matched
for name in bio_lookup.keys():
    sys.stderr.write( u"Could not match %s to an entry in Popolo JSON\n" % name )



# write out the new popolo data (tidied up a bit)
out_json = json.dumps(popolo_data, sort_keys=True, indent=4 )
out_json = re.sub(r'\s+\n', '\n', out_json)
out_json += "\n"
open( 'south-africa-popolo.json', 'w' ).write( out_json );
