#!/usr/bin/env perl

use strict;
use warnings;

use DBI;
use File::Slurp;
use JSON;

=pod

This script looks at selected tables in the original mzalendo database and pulls
out the data into json files that can then be processed with the Django code to
import into db.

=cut

# setup the json object
my $json = JSON->new->utf8(1)->pretty(1);

# setup where to create the various json files.
my $json_dir = '/tmp/mzalendo';
mkdir $json_dir;

# connect to the local mysql 'mzalendo' database
my $dbh = DBI->connect( "DBI:mysql:database=mzalendo", 'root', '' )
  || die "Could not connect to db...";

# dump some tables directly to JSON
dump_table_to_json($_)
  for (
    'answers',       'aspirantcomments',   'aspirants',
    'aspirantsites', 'bills',              'billstatus',
    'comments',      'commentstatus',      'committeemembers',
    'committees',    'constituencies',     'constituencymembers',
    'districts',     'hansards',           'ipBlocker',
    'members',       'membersites',        'membersterms',
    'membertypes',   'ministries',         'ministrymembers',
    'motions',       'motiontypes',        'offices',
    'parties',       'partyoffices',       'polling',
    'provinces',     'questioncategories', 'questions',
    'questiontypes', 'ranks',              'sitetypes',
    'sk2_blacklist', 'sponsors',           'status',
    'terms',
  );

=head2 dump_table_to_json

    dump_table_to_json( $table_name );

Outputs the content of the table to json in a file called '$table_name.json' in
'$json_dir'.

=cut

sub dump_table_to_json {
    my $table_name = shift;

    my $query = $dbh->prepare("select * from $table_name");
    $query->execute;

    my @rows = ();
    while ( my $row = $query->fetchrow_hashref ) {
        push @rows, $row;
    }

    write_file( "$json_dir/$table_name.json", $json->encode( \@rows ) );

    return 1;
}
