#!/usr/bin/env perl

=pod

This is a one-off import script to grab data from the mzalendo.com website and
output to STDOUT it as JSON for the Python scripts to import from. There are
several Perl deps that may be unmet on the server - this is intended to be run
on a dev box and the resulting JSON moved to a server and imported there.

Done in Perl not Python for conveniance :)

=cut

use strict;
use warnings;

use Web::Scraper;
use App::Cache;
use JSON;

my $url = 'http://mzalendo.com/Members.ListAll.php';

my $cache = App::Cache->new( { ttl => 3600 } );
my $html = $cache->get_code(
    $url, sub { `curl $url` }    # mzalendo.com 404's for LWP::UserAgent
);

my $mp_scraper = scraper {
    process 'table[width="773"] tr', 'mps[]', scraper {
        process 'th',                'raw_name',     'TEXT';
        process 'td',                'party',        'TEXT';
        process 'td:nth-of-type(2)', 'constituency', 'TEXT';
    };
};

my $mps_data = $mp_scraper->scrape($html)->{mps};

# throw away the first row - it is just headers
shift @$mps_data;

# rearrange the name and guess the middle names (80:20 rule - mostly right)
foreach my $mp (@$mps_data) {

    my $raw = $mp->{raw_name};

    # filter out titles eg "Kyalo, Philip Kaloki (Prof.)"
    $raw =~ s{\(.*?\)}{}g;

    my ( $last, $first, $middle ) =
      $raw =~ m{ \A \s* (.*?) ,\s* (\w+) \s* (.*?) \s* \z }xms;

    if ( !$last ) {
        ( $first, $last ) = split /\s+/, $raw, 2;
    }

    $mp->{first_name}  = $first  || '';
    $mp->{middle_name} = $middle || '';
    $mp->{last_name}   = $last   || '';
}

print JSON->new->pretty(1)->encode($mps_data);
