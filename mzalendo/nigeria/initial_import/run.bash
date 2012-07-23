#!/bin/bash

set -e
set -x

# Create the `var` directories - all the downloaded and generated files live in here

mkdir -p var/representatives var/senators

export ALL_REP_URL="http://www.nassnig.org/nass2/Princ_officers_all.php?title_sur=Hon."
export ALL_SEN_URL="http://www.nassnig.org/nass/Princ_officers_all.php?title_sur=Sen."

# gather all html content
cd var/representatives
../../representative_page_to_json.py profile.php*
cd ../..

cd var/senators
../../senator_page_to_json.py profile.php*
cd ../..


# process html into json
cd var/representatives
../../representative_page_to_json.py profile.php*
cd ../..

cd var/senators
../../senator_page_to_json.py profile.php*
cd ../..


# create a csv with all the areas that people cover
for DIR in var/representatives, var/senators: do
  cd $DIR;
  ./extract_areas.py *.json > areas.csv;
  cd ../..
done