# Pombola talking points




## Technical debt

Still on Django 1.3.* - should upgrade.

Nigeria is stuck on a different mapit branch and needs some database modifications to come back to master.



## Design:

MzKe currently has four designs on it:

- Election homepage:       http://info.mzalendo.com/
- General page:            http://info.mzalendo.com/organisation/odm/
- Blog:                    http://www.mzalendo.com/blog/
- Ad-traffic landing page: http://info.mzalendo.com/intro

There are also the cobrands:

- Kenya
- Nigeria
- Libya
- others not under our control (Tunisia?, Egypt?)

There are measures in place to allow countries to override specific templates
and CSS but these could be much improved. We need to decide haw theme-able the
codebase should be. If we want full theme ability then a different approach
might be needed. If we are happy forcing a fairly similar layout on all sites
then the current setup is probably ok and just needs tidying up (and documenting).

## Optional parts:

### Feature flips:

These are optional in the config and affect display on homepage.

- twitter feed
- blog rss
- poll daddy poll


### Optional apps:

- hansard
- projects
- place_data
- votematch (not completely finished yet)


### Should be optional apps

Currently assumed by other apps, but would be better as distinct pieces.

- scorecards
- feedback
- info (like staticpages)
- search (requires external search engine)


## MapIt integration

MapIt is embedded, and some parts assume it:

- maps on place pages
- the /map page (without mapit no places can be found)
- place hierarchies (derived from mapit boundaries, bit shaky)

There are several duplicates of places in MzKe, which is related to handling the
changing boundaries of various constituencies. This is probably counter
intuitive to most people. It was originally a hack done to allow data to be
gathered, but has persisted.



## Testing

Weak at best. Would be great to make it much more robust. Would really benefit
from having a good sized bit of sample test data - many of the things that go
wrong are interactions between the data from different apps.


## Cruft

The login system with facebook and twitter - no longer used.

Comments system is still in the database, but not used.

There is a tasks app that was originally intended for crowdsourcing. Now not
used.


## User support

There is much to be done here. Currently the install instructions are poor, and
there is no guide to altering the design.

There is also an operations manual which is intended to cover how to run a site
like Mz but it's not received much attention.


## Admin interface

Currently only just dealing with the complexities of the links between the various data models.







