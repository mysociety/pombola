# Interests Register

This is a simple app that is currently mostly a set of models and an import
script. It was developed for the South African Pombola site, but should be
general enough to be easily extendeable.

## TODO items

- Tests, not done yet as there was not much to test
- Views, currently the only display of this data is in the `south_africa` app on the person detail page.
- URLs - once the views are done.
- Track items that occur in several releases.

## Data model

### Releases

I think that the way that the members' interests are usually published is in
installments, either annually or some other regularish period. Each of these
publications is a `release` which has a name and a date.

### Entries

An `entry` is a collection of related data for a given release, person and
category. An entry is made up of line items, which are just key value pairs.
This was done for ease with the South African data but should be quite
extendable. A text field could be added directly to the entry model if the
published data is just a free text box.

## Import script and JSON format

To import the South African data an intermediate JSON format was created - see
the `sample_source.json` file for the format. It is quite verbose, but should
be quite easy to produce from scripts. The import command
`interests_register_import_from_json` will create missing releases and
categories as they are encountered. It has some rudimentary prohection against
loading in duplicates. There are plenty of improvements that can be made.

## Views

It would be nice have a way to navigate around the interests and explore them.
