# General deployment notes

(there are site specific notes at the end)

## N > 1 server deployment

This is currently not possible.

The search index is stored on file locally on the machine. It is updated
whenever there is a change to a person, organisation or place, and when the
hansard imports happen.
[see issue #524](https://github.com/mysociety/mzalendo/issues/524)

# Site specific

These are notes about changes that need to happen for deployments that can not
be automated using migrations etc.

## Nigeria

In requirements.txt the mapit repo used is now on the branch `7-area-unions`. It
should probably be `master` instead, or `pypi` as it was. The union branch was
used to accommodate the nigerian boundaries - where some of them are formed of
unions of lesser ones ('Senatorial Districts' are composed of 'Federal
Constituencies' if memory serves).

Before merging the latest changes to the nigeria branch, or switching the
shineyoureye site to master, this needs to be resolved.


The Alias for robots.txt should be removed from the server http.conf so that the robots.txt can be templated.
