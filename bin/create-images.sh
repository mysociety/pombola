#!/bin/sh

# For every PDF in the current directory, this script creates a
# directory based on its basename, and fills that directory with one
# PNG per page (called page-001.png, page-002.png, etc.) rendered at
# 600dpi resolution.

# This is useful for taking all the PDFs of party lists of aspirants
# and converting them into more workable formats.

set -e

for p in *.pdf
do
    d="${p%.pdf}"
    mkdir -p "$d"
    echo doing "$d"
    ( cd "$d" && gs -sOutputFile=page-%03d.png \
                    -dNOPAUSE \
                    -dSAFER \
                    -dBATCH -q \
                    -sDEVICE=pnggray \
                    -r600 \
                    -dGraphicsAlphaBits=4 \
                    -dTextAlphaBits=4 \
                    ../"$p" )
done
