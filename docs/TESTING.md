# Running the Pombola tests

## Running the complete test suite (i.e. for all supported countries)

There is Django applications for each of the countries for which
we support running Pombola. To run the tests that are specific
to each of these countries, as well as the generic tests
relevant to all countries, you can run:

    ./run-tests

## Running the tests for a particular country

You can see in the output of `./run-tests` the commands that are
used to run the tests that are specific to a particular
country. For example, to run all the tests for South Africa, you
would run:

    ./manage.py test --settings='pombola.settings.tests_south_africa'

## Running tests selectively

Sometimes you want to just try one test method. You can do this
for a generic test, for example, with:

    ./manage.py test pombola.core.tests.test_models:PositionCurrencyTest.test_from_past_still_current

Note that there must be a colon separating the module from the
class name.

Similarly, you can run a country-specific test by including the
settings module for that country. For example:

    ./manage.py test --settings='pombola.settings.tests_south_africa' \
        pombola.south_africa.tests:SAAttendanceDataTest.test_get_attendance_stats

## Speeding up repeated test runs

So long as you are only running tests with a single settings
module (i.e. not using `./run-tests`) you can dramatically speed
up the second and subsequent test runs by supplying the
`--keepdb` option to `test`, like:

    ./manage.py test --keepdb \
        pombola.core.tests.test_models:PositionCurrencyTest.test_from_past_still_current

... because much of the time in running the tests is taken up
with running the database migrations. Note that if you switch to
running tests selectively with a different settings module,
you'll have to drop the `--keepdb` on the first run, and say
"yes" when it offers to delete the test database. This is
because the settings for different countries cause different
migrations to be run, so you can't necessarily re-run the tests
with the same database.
