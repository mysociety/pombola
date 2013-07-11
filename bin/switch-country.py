#!/usr/bin/env python
# coding=UTF-8

# If you have a standard Mzalendo setup (see below) and need to switch
# between developing for different countries, this script can be
# useful for making that switch simply.  It assumes that you have the
# following directory hierarchy, config files and symlinks set up:
#
# .
# ├── collected_static
# ├── media_root -> media_root.kenya
# ├── media_root.kenya
# ├── media_root.nigeria
# ├── media_root.south-africa
# ├── mzalendo
# │   ├── .git
# │   ├── bin
# │   ├── conf
# │   │   ├── general-kenya.yml
# │   │   ├── general-nigeria.yml
# │   │   ├── general-south-africa.yml
# │   │   └── general.yml -> general-kenya.yml
# │   ├── mzalendo
# │   │   ├── core
# ...

import os
import sys

script_directory = os.path.dirname(os.path.realpath(sys.argv[0]))
mzalendo_directory = os.path.join(script_directory, '..', '..')
mzalendo_directory = os.path.normpath(mzalendo_directory)

available_mzalendi = ('nigeria', 'kenya', 'south-africa')

def usage_and_exit():
    print >> sys.stderr, "Usage: %s <COUNTRY>" % (sys.argv[0],)
    print >> sys.stderr, "... where country is one of:"
    for country in available_mzalendi:
        print >> sys.stderr, "  ", country
    sys.exit(1)

if len(sys.argv) != 2:
    usage_and_exit()

requested = sys.argv[1]

if requested not in available_mzalendi:
    usage_and_exit()

media_root_symlink = os.path.join(mzalendo_directory, 'media_root')
general_yml_symlink = os.path.join(mzalendo_directory, 'mzalendo', 'conf', 'general.yml')

media_root_target = 'media_root.' + requested
general_yml_target = 'general-' + requested + '.yml'

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
    os.symlink(target_filename, symlink)

for target, symlink in ((media_root_target, media_root_symlink),
                        (general_yml_target, general_yml_symlink)):
    switch_link(symlink, target)
