# Useful background for working on Pombola

The intention of this document is to set out some general
principles, background and history which might be useful in
maintaining Pombola.

I hope this is accurate at the time of writing but please make a
pull request to fix any errors you find, or to make
improvements.

## History

Pombola was original developed by Edmund von der Burg to provide
a parliamentary monitoring site like TheyWorkForYou for
Kenya. (The TheyWorkForYou codebase has so much UK-specific code
in it that porting it to other countries is a massive effort -
OpenAustralia and Kildare Street did so but that's pretty
extraordinary.) Being developed in Django meant that this
codebase was also much easier for most of our developers to work
on than the rather old PHP of TheyWorkForYou.

The working model of these sites is that we provide development,
design, hosting and user research support, but the site is run
by people or an organization (typically an NGO like Mzalendo or
PMG) in the country itself.

Since then it has been extended to support other
countries. These are / were:

* [Mzalendo](http://info.mzalendo.com) in Kenya run by Mzalendo.
* [People's Assembly](https://www.pa.org.za) in South Africa run
  by PMG.
* [Odekro](http://www.odekro.org/) in Ghana. This was a fork of
  Pombola, but it seems that they've now switched to another
  system. (See below for notes on handling forks of the codebase
  better.)
* [ShineYourEye](https://www.shineyoureye.org) run by EiE
  Nigeria. This has since been migrated away from Pombola to be
  a largely static site generated from
  https://github.com/theyworkforyou/shineyoureye-sinatra - the
  old Pombola site is still available at a subdomain of
  shineyoureye.org since some data the static site build
  requires is only maintained there. We are currently going
  through some work with EiE to redesign and change the aim of
  that site.
* Libya: I don't know the history of this, but at some point we
  hosted a Pombola for Libya at watani.org.ly, but that appears
  never to have been taken forward.

There were a couple of other installations in other countries
which broke the AGPL by not making their changes to the source
code available, and wouldn't respond to our requests for them to
do that. [I can't easily find a record of which these sites were
at the moment.]

At the moment the live Pombola sites that we're focussed on
supporting are Mzalendo (Kenya) and People's Assembly (South
Africa).

## Switching between countries

We used to support switching between countries in the development
environment, but as we're now moving towards country-specific forks
this is no longer supported. See the
[Vagrant section of INSTALL.md](INSTALL.md#vagrant) for details on how
to construct a development environment for a given country.

## Architectural direction

### Move useful Django apps into Python packages

We've been making an effort to package up some of Pombola's code
into packages that can be installed from PyPI. This is because:

* It reduces the size of this codebase
* We can create generically useful Django apps this way
* It encourages a clear separation of generic and
  Pombola-specific functionality

Some examples of this are:

* https://github.com/mysociety/django-images
* https://github.com/mysociety/django-info-pages
* https://github.com/mysociety/django-slug-helpers

It would be good to continue in this direction. For example, the
pombola.writeinpublic app would be another good candidate.

Another aspect of this would be to make the core views and
models of Pombola into a django-pombola-core package. This leads
onto the next aim:

### Move to one repository per country

A number of mySociety projects have had a problem where changes
in a country-specific fork of the code was never merged back, or
could only be merged back at huge effort on our part. And if we
did that, the fork would immediately start drifting again.

This can happen because the maintainer of the fork wasn't
conscious of the importance of making regular pull requests back
to upstream, or it's just too hard for them to do: you need to
understand quite a bit about git and the code of the project to
do this well.

In Pombola's case, the Ghana fork (Odekro) was the clearest case
where this has been a problem.

I think that one good way of addressing this problem is to use
the model where the core, country-independent code is packaged
up and made a dependency of a country-specific repository. This
removes the need for things like the bin/switch-country.py
script, the `Vagrantfile` would only have to worry about
setting up one country, it'd be easier to figure out what files
you need to change to update a template, say, etc. etc.

This means that in a case like Odekro, the country-specific
repository would be entirely maintained by them and the only
version skew issues we need to worry about are:
* sometimes making a pull request to update the version of the
  django-pombola-core package in use
* dealing with requests to change the functionality in
  django-pombola-core.

## Abandoned plans

At one point it was our firm plan to migrate Pombola to use the
models in
[django-popolo](https://github.com/mysociety/django-popolo)
instead of the Pombola core models. This was
[issue 1594](https://github.com/mysociety/pombola/issues/1594). Unfortunately
this ended up taking so long that we put it to one side, and I'm
not convinced this is actually worthwhile, unless we have much
more development budget for Pombola. The motivation for this was
that it we could then plug in other Django applications that
used the django-popolo models: one of these, SayIt, is already
used by People Assembly, which would simplify the interface
between Pombola and SayIt. Another example might have been
WriteInPublic, but since that needs to support multiple sources
of Popolo data, (via multiple-django-popolo-sources) in fact
that wouldn't be straightforward. This means that at the moment
we don't have a compelling example of another Django application
that could be added as result of the #1594 work, and there's a
lot involved in it. So at the moment, we're considering that
work abandoned.

## Data modelling problems

When trying to use Mzalendo and People's Assembly as a data
source for EveryPolitician, we found lots of problems that arose
from the generic data model allowing lots of different ways of
representing the positions politicians hold. It's difficult at
the moment to enforce particular ways of modelling this, and
because our partners tend to enter data one person at a time,
it's hard to spot inconsistencies (experience shows us that it's
much easier to spot these things if you see multiple people at
once, in a table, say). You can find many examples of these
kinds of problems here:

https://github.com/mysociety/pombola/issues?q=is%3Aopen+is%3Aissue+label%3Adata

## Frontend development

It's worth bearing in mind that lots of the styles and templates
in pombola.core are overridden in pombola.kenya and
pombola.south_africa, so much of it is now unused (but would
provide useful defaults if you were to set up a new site).

## Country-specific notes

A key difference between Mzalendo and People's assembly is how
they handle scraping and presenting proceedings from parliament.

* Mzalendo: everything's in the pombola.hansard
  application. Name resolution and correction is done using the
  Alias model.
* People's Assembly: scrapers are in an app called
  'za-hansard' which produce JSON. That JSON is imported into
  SayIt models. SayIt's person model (from django-popolo) is
  linked to Pombola models using the PombolaSayItJoin model from
  pombola_sayit. There's more below about za-hansard.

Another notable difference is how user comments on the site are
handled:

* Mzalendo uses Disqus
* People's Assembly uses Facebook

### Kenya

#### Deprecated or unmaintained

Various features of the site no longer are used or have the data
to support them. For example:

* `scorecards` (Scorecards for MPs or constituencies (based on
  CDF data)) - as far as I know we no longer have up-to-date
  data to support this.
* `votematch` - We developed this as a voter advice application
  feature for the site, but it turned out that we couldn't find
  enough questions that would fairly reflect policy differences
  between the candidates based on the from published manifestos.
* `feedback` - There is an option to leave feedback on most
  pages of the site, which should then be addressed by the site
  maintainers. And email reminder about this is generated from
  cron each day. However, I'm not sure that anyone is actually
  dealing with these reports any more.
