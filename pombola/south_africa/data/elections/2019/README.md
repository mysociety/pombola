# 2019 Elections data

This directory contains the data files that were used to load the candidates
into the database.

## National.csv

List of the names of all national and regional candidates, along with the
party they're standing for.

This data was imported with the
`south_africa_import_election_candidates_2019` management command.

## Provincial-*.csv

The provincial candidates for NCOP. These were imported with the
`south_africa_import_election_candidates_2019` command.

## parties.csv

Mapping between pombola party names/slugs and the names that appear in the
candidates file. This is for the parties of the National, Regional and
Provincial candidates. Missing parties can be created with the
`south_africa_create_new_parties_for_election_2019` management command.
