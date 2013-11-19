The speeches subsystems
=======================

The South African Pombola instance requires a number of interrelated components
to be able to import speech content such as Hansard transcripts, Question &
Answers, and Committee minutes.

While we have been working on these interlocking components, we have mostly had
entries in `requirements.txt` like:

    -e git+git://github.com/mysociety/popit-resolver@master#egg=popit-resolver  
        # NOTE - when changing remember to remove the repo from virtualenv!

This has been required to allow a simple `pip install -r requirements.txt` to
update the requirements.  It has also sometimes been convenient to develop code
in one or more of the subsystems by editing it directly in the virtualenv (which 
is a git repo, as per the `-e` line above).

SayIt (speeches)
----------------

Speeches are stored in SayIt's `speeches` app.  This app must currently be set 
in OPTIONAL_APPS, but is configured in pombola/south_africa/urls.py to be
mounted under:

    /hansard
    /committee  ... as appropriate, the top-level URL gives index view
    /question

        /<pk>         # the section (e.g. debate, committee, or QA date/topic)
        /speech/<pk>  # individual speech
        /speaker<pk>  # link back to pombola person (see "Name Resolution"
                      # section below)

The most recent speeches of all 3 types are also listed under

    /person/<slug>

and are browsable under

    /person/<slug>/appearances/hansard
    /person/<slug>/appearances/committee
    /person/<slug>/appearances/question

In all these cases, we use django template's namespacing to make sure that the
sayit content all resolves back to the correct type of content (Hansard etc.)

za-hansard
----------

All the code to parse South African parliamentary content lives here.  You can
access all the functionality using management commands.  Some of these commands
will import the parsed speeches into the associates SayIt DB.

Hansard parsing uses the following commands:

    za_hansard_check_for_new_sources
    za_hansard_run_parsing
    za_hansard_load_into_sayit

Committee minutes uses just one command, with flags to perform the various phases

    za_hansard_pmg_scraper

Likewise Question & Answer uses a single command, with various flags to perform
the different phases.  (There are far more phases, due to processing Questions
and Answers separately, and later matching them together.)

    za_hansard_q_and_a_scraper

All these commands can be run from pombola using:

    (pombola) $ bin/update_za_hansard.bash

popit-django
------------

This component is currently a fairly lightweight way of getting data from a popit
instance into a bare-bones table (name, photo, popit_id).  Within Pombola, the
app is only really used as part of the mapping between Pombola person and Speaker
objects, and as a requirement for popit-resolver.

popit-resolver
--------------

This component is used to resolve names such as "Annette Steyn" or "Mrs A Steyn"
or "The Minister for Agriculture, Forestry, and Fisheries" to the same person.

The `popit_resolver_entityname` table contains mappings from various forms of the
name to the popit_person object.  The names are constructed from popit's persons,
memberships, and organizations collections as follows:

    - full name
    - name with initials
    - if the person belongs to a party:
        - full name + (party name)
        - name with initials + (party name)
    - for every membership
        - role label + organization name

The party and membership roles are potentially constrained by start and end dates.

Popit-resolver uses ElasticSearch to find matches and, if available, returns the
best possible match.

Popit resolver is initialised with a management command:

    $ python manage.py  popit_resolver_init --popit-api-url=http://za-peoples-assembly.popit.mysociety.org/api/v0.1

It may sometimes be useful to use the Elasticsearch management commands too, such as

    $ python manage.py  update_index

Note that all the components which use popit-resolver now will include in their
settings.py some code to update the `HAYSTACK_CONNECTIONS['default']['INDEX_NAME']`
when running as a test.  (Otherwise live and test data will both be in the index,
and there will be great confusion.)

Name Resolution
===============

The various subsystems have several overlapping notions of "person" in their
database schemas:

    pombola:      core_person
    sayit:        speeches_speaker
    popit-django: popit_person

Pombola and popit-django are both fed (originally) from the same canonical data
in pombola/south_africa/data/south-africa-popolo.json
However the core Pombola data-structure hasn't been updated to include a
reference to the popit person.  Instead, pombola supports generic identifier tags,
and pombola/south_africa/views.py has mapping functions in PersonSpeakerMappings
to map between these objects like so:

    core_person
      (id)
        |
      (object_id)
    core_identifier -- content_type=django_content_type for Person
      (scheme + identifier)
        |
      (popit_id)
    popit_person
      (id)
        |
      (person_id)
    speeches_speaker

The scheme is 'org.mysociety.za' and the primary key `(schema + identifier)` has
to be matched with string concatenation.
https://github.com/mysociety/pombola/issues/963 has some example SQL for this.
