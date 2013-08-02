#!/usr/bin/env python

import json
import myreps
import parl
import manual
import committees

data = myreps.parse()
data = parl.parse(data)
data = manual.parse(data)
data = committees.parse(data)

# Sort output
data['organizations'] = data['organizations'].values()
data['persons'] = data['persons'].values()
data['persons'].sort(key=lambda p: ([ x for x in p['memberships'] + [ { 'organization_id': 'house/XXX' } ]  if 'house' in x['organization_id'] ][0]['organization_id'], p['family_name'], p['given_names']))
data['organizations'].sort(key=lambda p: ('executive' not in p['id'], 'house' not in p['id'], p['name']))

print json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
