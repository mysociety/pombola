#!/usr/bin/env python

# This script walks through all files under the current directory,
# looking for those called page-001.png, page-002.png, etc.  (If a
# version called page-001.rotated.png, etc. is also present, that us
# used as in put in preference.)  For each page the script uses
# "convert -deskew '40%'" and then "unpaper" to remove scanning
# artefacts.  (ImageMagick does better than unpaper on large skews.)

import os, re
from subprocess import check_call

original_page_re = re.compile('^(page-[0-9]+)\.png')

for root, dirs, files in os.walk('.'):

    def full(filename):
        return os.path.join(root, filename)

    def exists(filename):
        return os.path.exists(full(filename))

    for filename in sorted(files):

        m = original_page_re.search(filename)
        if not m:
            continue

        print "====", full(filename)

        filename_to_use = filename
        basename = m.group(1)

        rotated_filename = "%s.rotated.png" % (basename,)
        if exists(os.path.join(rotated_filename)):
            filename_to_use = rotated_filename

        deskewed_filename = "%s-deskewed.png" % (basename,)
        if not exists(deskewed_filename):
            print "converting", filename_to_use, "to", deskewed_filename
            check_call(["convert",
                        "-deskew",
                        "40%",
                        full(filename_to_use),
                        full(deskewed_filename)])

        pnm_version = "%s-deskewed.pnm" % (basename,)
        unpapered_pnm_version = "%s-deskewed-unpapered.pnm" % (basename,)
        unpapered_filename = "%s-deskewed-unpapered.png" % (basename,)

        if not exists(pnm_version):
            print "converting", deskewed_filename, "to", pnm_version
            with open(full(pnm_version), "w") as fp:
                check_call(["pngtopnm",
                            full(deskewed_filename)],
                           stdout=fp)

        if not exists(unpapered_pnm_version):
            print "unpapering", pnm_version, "to", unpapered_pnm_version
            check_call(["unpaper",
                        full(pnm_version),
                        full(unpapered_pnm_version)])

        if not exists(unpapered_filename):
            print "converting", unpapered_pnm_version, "to", unpapered_filename
            with open(full(unpapered_filename), "w") as fp:
                check_call(["pnmtopng",
                            full(unpapered_pnm_version)],
                           stdout=fp)

        os.remove(full(pnm_version))
        os.remove(full(unpapered_pnm_version))
