#!/usr/bin/env perl

use strict;
use warnings;

use DBI;
use File::Slurp;
use JSON;
use Text::CSV;

=pod

This script looks at selected tables in the original mzalendo database and pulls
out the data into json files that can then be processed with the Django code to
import into db.

=cut

# connect to the local mysql 'mzalendo' database
my $dbh = DBI->connect( "DBI:mysql:database=mzalendo", 'root', '' )
  || die "Could not connect to db...";

my $csv = Text::CSV->new;

my $query = $dbh->prepare("select * from members");
$query->execute;

my @rows = ();
while ( my $row = $query->fetchrow_hashref ) {

    # use Data::Dumper;
    # local $Data::Dumper::Sortkeys = 1;
    # warn Dumper($row);

    my @business_or_political_fields = ( 'Duties', 'Profile' );
    my @education_fields = (
        'OtherEducation',     'PrimaryEducation',
        'SecondaryEducation', 'UniversityEducation'
    );

# output: person_id, name, field, import, job_title, org, place, start, end, line

    foreach my $field (@education_fields) {
        foreach my $line ( split /\n+/, $row->{$field} ) {

            $line =~ s{\s+}{ }g;
            $line =~ s{^\s+}{}g;
            $line =~ s{\s+$}{}g;

            next
              if $line !~ m{\S}
                  or $line eq 'Employment History';

            my $import    = 'n';
            my $job_title = '';
            my $org       = '';
            my $place     = '';
            my $start     = '';
            my $end       = '';

            my $date = '\w*\s*\d{4}|date';

            if ( my @matches =
                $line =~ m{($date)\s*(?:-|to)\s*($date):?\s*(.*)}i )
            {
                ( $start, $end, my $rest ) = @matches;
                ( $job_title, $org ) = split /,/, "$rest,", 2;
            }
            elsif ( my @matches2 = $line =~ m{($date)\s*:\s*(.*)}i ) {
                ( $start, my $rest ) = @matches2;
                ( $job_title, $org ) = split /,/, "$rest,", 2;
            }
            else {
                ( $job_title, $org ) = split /,/, "$line,", 2;
            }
            $org =~ s{,\s*$}{};
            
            

            $csv->print(
                \*STDOUT,
                [
                    $row->{MemberID}, $row->{Fullnames}, $field, $import,
                    $job_title, $org, $place, $start, $end, $line
                ]
            );
            print "\n";

        }
    }

}

