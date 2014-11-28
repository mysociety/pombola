#!/usr/bin/env python
# coding=UTF-8

# If you have a standard Pombola setup (see below) and need to switch
# between developing for different countries, this script can be
# useful for making that switch simply.  It assumes that you have the
# following directory hierarchy, config files and symlinks set up:
#
# .
# ├── collected_static
# ├── media_root
# ├── media_root.ghana
# ├── media_root.kenya -> media_root
# ├── media_root.nigeria
# ├── media_root.south-africa
# ├── media_root.zimbabwe
# ├── pombola
# │   ├── .git
# │   ├── bin
# │   ├── conf
# │   │   ├── general-ghana.yml
# │   │   ├── general-kenya.yml
# │   │   ├── general-nigeria.yml
# │   │   ├── general-south-africa.yml
# │   │   ├── general-zimbabwe.yml
# │   │   └── general.yml -> general-kenya.yml
# │   ├── pombola
# │   │   ├── core
# ...
#
# Note that we can't just have a symlink media_root -> media_root.kenya
# since the path for file uploads is checked after resolving symlinks
# and a SuspiciousOperation exception is raised if the path doesn't
# begin with the MEDIA_ROOT path.
#
# Instead we keep a media_root.kenya -> media_root symlink just to
# indicate where the media_root directory should be moved back to on
# switching country.

import os
import sys

script_directory = os.path.dirname(os.path.realpath(sys.argv[0]))
pombola_directory = os.path.join(script_directory, '..', '..')
pombola_directory = os.path.normpath(pombola_directory)

available_pombolas = ('ghana', 'nigeria', 'kenya', 'south-africa', 'zimbabwe')

def usage_and_exit():
    print >> sys.stderr, "Usage: %s <COUNTRY>" % (sys.argv[0],)
    print >> sys.stderr, "... where country is one of:"
    for country in available_pombolas:
        print >> sys.stderr, "  ", country
    sys.exit(1)

if len(sys.argv) != 2:
    usage_and_exit()

requested = sys.argv[1]

if requested not in available_pombolas:
    usage_and_exit()

general_yml_symlink = os.path.join(pombola_directory, 'pombola', 'conf', 'general.yml')
general_yml_target = 'general-' + requested + '.yml'

media_root_path = os.path.join(pombola_directory, 'media_root')
media_root_path_requested = media_root_path + "." + requested
media_root_target = 'media_root.' + requested

for path in (media_root_path,
             media_root_path_requested):
    if not os.path.exists(path):
        raise Exception, "Couldn't find: " + path

def switch_link(symlink_filename, target_filename):
    if not os.path.islink(symlink_filename):
        print >> sys.stderr, "%s was not a symlink, and should be" % (symlink_filename,)
        sys.exit(1)
    full_target_filename = os.path.join(os.path.dirname(symlink_filename),
                                        target_filename)
    if not os.path.exists(full_target_filename):
        print >> sys.stderr, "The intended target of the symlink (%s) didn't exist" % (target_filename,)
        sys.exit(1)
    os.unlink(symlink_filename)
    os.symlink(target_filename, symlink_filename)

switch_link(general_yml_symlink, general_yml_target)

# Check that we have the existing symlink set up to indicate which
# country's media_root was currently in use:

old_country = None

for country in available_pombolas:
    possible_symlink = media_root_path + '.' + country
    if os.path.islink(possible_symlink):
        resolved = os.readlink(possible_symlink)
        if resolved == 'media_root':
            if old_country:
                message = "Found multiple countries' media_root symlinks pointing to media_root:"
                message += " %s and %s" % (old_country, country)
                raise Exception, message
            else:
                old_country = country

if not old_country:
    raise Exception, "Found no symlink indicating the existing country"

# Remove the symlink indicating what the old country was, and move
# media_root back to that path:

old_country_path = media_root_path + "." + old_country
os.unlink(old_country_path)
os.rename(media_root_path, old_country_path)

# Now move the new country's media_root into position, and
# create the sylink:

os.rename(media_root_path + "." + requested, media_root_path)
os.symlink("media_root", media_root_path_requested)
