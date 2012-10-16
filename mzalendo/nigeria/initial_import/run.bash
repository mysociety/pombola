#!/bin/bash

set -e
set -x

# # Create the `var` directories - all the downloaded and generated files live in here
# 
# mkdir -p var/representatives var/senators
# 
# export ALL_REP_URL="http://www.nassnig.org/nass2/Princ_officers_all.php?title_sur=Hon."
# export ALL_SEN_URL="http://www.nassnig.org/nass/Princ_officers_all.php?title_sur=Sen."
# 
# # fetch all html
# 
# cd var/representatives
# curl -o all.html $ALL_REP_URL
# ../../extract_urls.py < all.html > urls.txt
# wget -B $ALL_REP_URL -i urls.txt 
# cd ../..
# 
# cd var/senators
# curl -o all.html $ALL_SEN_URL
# ../../extract_urls.py < all.html > urls.txt
# wget -B $ALL_SEN_URL -i urls.txt 
# cd ../..
# 
# # gather all html content
# cd var/representatives
# ../../representative_page_to_json.py profile.php*
# cd ../..
# 
# cd var/senators
# ../../senator_page_to_json.py profile.php*
# cd ../..
# 
# 
# # process html into json
# cd var/representatives
# ../../representative_page_to_json.py profile.php*
# cd ../..
# 
# cd var/senators
# ../../senator_page_to_json.py profile.php*
# cd ../..
# 

# create a csv with all the areas that people cover
for DIR in var/representatives var/senators; do
  cd $DIR;
  ../../extract_areas.py *.json > areas.csv;
  cd ../..
done


# add all the people to the database
find var -name *.json | xargs ./import_people_from_json.py

# import all the positions from the csv to the database
./import_positions_from_csv.py *.csv