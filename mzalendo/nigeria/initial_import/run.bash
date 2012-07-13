#!/bin/bash

set -e
set -x

# Create the `var` directories - all the downloaded and generated files live in here

mkdir -p var/representatives var/senators

export ALL_REP_URL="http://www.nassnig.org/nass2/Princ_officers_all.php?title_sur=Hon."
export ALL_SEN_URL="http://www.nassnig.org/nass/Princ_officers_all.php?title_sur=Sen."

cd var/representatives
curl -o all.html $ALL_REP_URL
../../extract_urls.py < all.html > urls.txt
wget -B $ALL_REP_URL -i urls.txt 
../../representative_page_to_json.py profile.php*
cd ../..

cd var/senators
curl -o all.html $ALL_SEN_URL
../../extract_urls.py < all.html > urls.txt
wget -B $ALL_SEN_URL -i urls.txt 
../../senators_page_to_json.py profile.php*
cd ../..

