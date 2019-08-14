import os, sys
import re
import httplib2
import calendar

from django.db import models
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from speeches.models import Section

HTTPLIB2_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/601.4.4 (KHTML, like Gecko) Version/9.0.3 Safari/601.4.4'
}

if 'ON_HEROKU' not in os.environ:
    # check that the cache is setup and the directory exists
    for setting_name in ('HANSARD_CACHE',
                         'COMMITTEE_CACHE',
                         'ANSWER_CACHE',
                         'QUESTION_CACHE',
                         'ANSWER_JSON_CACHE',
                         'QUESTION_JSON_CACHE'):
        try:
            directory = os.path.join(getattr(settings, setting_name))
            if not os.path.exists(directory):
                os.makedirs(directory)
        except AttributeError:
            raise ImproperlyConfigured("Could not find {0} setting - please set it".format(setting_name))

# EXCEPTIONS

class SourceUrlCouldNotBeRetrieved(Exception):
    pass

class SourceCouldNotParseTimeString(Exception):
    pass


class SourceQuerySet(models.query.QuerySet):
    def requires_processing(self):
        return self.filter( last_processing_attempt=None )

    def requires_completion(self, retry_download=False):
        objects = self.filter( last_processing_success=None )
        if not retry_download:
            objects = objects.filter( is404=False )
        return objects


class Source(models.Model):
    """
    Sources of the hansard transcripts

    For example a Word transcript.
    """

    title           = models.CharField(max_length=200)
    document_name   = models.CharField(max_length=200) # bah, SHOULD be unique, but apparently isn't
    document_number = models.CharField(unique=True, max_length=200)
    date            = models.DateField()
    url             = models.URLField(max_length=1000)
    is404           = models.BooleanField( default=False )
    house           = models.CharField(max_length=200)
    language        = models.CharField(max_length=200)

    last_processing_attempt = models.DateTimeField(blank=True, null=True)
    last_processing_success = models.DateTimeField(blank=True, null=True)

    last_sayit_import = models.DateTimeField(blank=True, null=True)
    sayit_section = models.ForeignKey(Section, blank=True, null=True, on_delete=models.PROTECT,
        help_text='Associated Sayit section object, if imported')

    objects = SourceQuerySet.as_manager()

    class Meta:
        ordering = [ '-date', 'document_name' ]


    def __unicode__(self):
        return self.document_name


    def delete(self):
        """After deleting from db, delete the cached file too"""
        cache_file_path = self.cache_file_path()
        super( Source, self ).delete()

        if os.path.exists( cache_file_path ):
            os.remove( cache_file_path )


    def file(self, debug=False):
        """
        Return as a file object the resource that the url is pointing to.

        Should check the local cache first, and fetch and store if it is not
        found there.

        Raises a SourceUrlCouldNotBeRetrieved exception if URL could not be
        retrieved.
        """
        cache_file_path = self.cache_file_path()

        found = os.path.isfile(cache_file_path)

        if debug:
            print >> sys.stderr, "%s (%s)" % (cache_file_path, found)

        # If the file exists open it, read it and return it
        if found:
            return cache_file_path

        # If not fetch the file, save to cache and then return fh
        h = httplib2.Http()
        url = 'http://www.parliament.gov.za/live/' + self.url

        def request_url(url):
            if debug:
                print >> sys.stderr, 'Requesting %s' % url
            (response, content) = h.request(url, headers=HTTPLIB2_HEADERS)
            if response.status != 200:
                raise SourceUrlCouldNotBeRetrieved("status code: %s, url: %s" % (response.status, self.url) )
            self.is404 = False
            self.save()
            return (response, content)

        try:
            (response, content) = request_url(url)
        except SourceUrlCouldNotBeRetrieved as e:
            try:
                if not url[-4:] == '.doc':
                    (response, content) = request_url(url + '.doc')
                    self.url = self.url + '.doc'
                    self.save()
                else:
                    raise e
            except:
                raise e

        if not content:
            raise SourceUrlCouldNotBeRetrieved("WTF?")
        with open(cache_file_path, "w") as new_cache_file:
            new_cache_file.write(content)

        return cache_file_path

    @property
    def section_parent_headings(self):
        return [
            "Hansard",
            str(self.date.year),
            calendar.month_name[self.date.month],
            "%02d" % self.date.day,
        ]

    def cache_file_path(self):
        """Absolute path to the cache file for this source"""

        id_str= "%05u" % self.id

        # do some simple partitioning
        # FIXME - put in something to prevent the test suite overwriting non-test files.
        aaa = id_str[-1]
        bbb = id_str[-2]
        cache_dir = os.path.join(settings.HANSARD_CACHE, aaa, bbb)

        # check that the dir exists
        if not os.path.exists( cache_dir ):
            os.makedirs( cache_dir )

        d = self.date.strftime('%Y-%m-%d')

        # create the path to the file
        cache_file_path = os.path.join(cache_dir, '-'.join([d, id_str, self.document_name]))
        return cache_file_path

    def xml_file_path(self):
        xml_file_path = '%s.xml' % self.cache_file_path()
        if os.path.isfile(xml_file_path):
            return xml_file_path
        return None

class PMGCommitteeReport(models.Model):
    """
    Committe reports, scraped from PMG site
    """
    premium         = models.BooleanField(default=None)
    processed       = models.BooleanField(default=None)
    meeting_url     = models.TextField()
    meeting_name = models.TextField(blank=True, null=True)
    committee_url = models.URLField(blank=True, null=True)
    committee_name = models.TextField(default='')
    meeting_date = models.DateField(blank=True, null=True)

    # For anything sourced from the PMG API, these two fields should
    # identify the meeting event:
    api_committee_id = models.IntegerField(null=True, blank=True)
    api_meeting_id = models.IntegerField(null=True, blank=True)

    last_sayit_import = models.DateTimeField(blank=True, null=True)
    sayit_section = models.ForeignKey(Section, blank=True, null=True, on_delete=models.PROTECT,
        help_text='Associated Sayit section object, if imported')

    def old_meeting_url(self):
        return self.meeting_url and 'api.pmg.org.za' not in self.meeting_url


class PMGCommitteeAppearance(models.Model):
    """
    Committe appearances, scraped from PMG site
    """
    party           = models.TextField()
    person          = models.TextField()
    report = models.ForeignKey(PMGCommitteeReport,
        null=True,
        on_delete=models.CASCADE,
        related_name='appearances')
    text            = models.TextField()

house_choices = (
    ('N', 'National Assembly'),
    ('C', 'National Council of Provinces'),
    )

class Answer (models.Model):
    # Various values that the processed_code can have
    PROCESSED_PENDING = 0
    PROCESSED_OK = 1
    PROCESSED_HTTP_ERROR = 2

    PROCESSED_CHOICES = (
        ( PROCESSED_PENDING, 'pending'),
        ( PROCESSED_OK, 'OK' ),
        ( PROCESSED_HTTP_ERROR, 'HTTP error'),
    )

    #------------------------------------------------------------
    document_name = models.TextField()

    # The next few fields are all inferred from document_name

    # At least one of number_oral and number_written must be non-null
    # They both could be non-null if the question was at some point transferred.
    oral_number = models.IntegerField(null=True, db_index=True)
    written_number = models.IntegerField(null=True, db_index=True)

    # The president and vice president get their own question number sequences for
    # oral questions.
    president_number = models.IntegerField(null=True, db_index=True)
    dp_number = models.IntegerField(null=True, db_index=True)

    date = models.DateField()
    year = models.IntegerField(db_index=True)
    house = models.CharField(max_length=1, choices=house_choices, db_index=True)
    #------------------------------------------------------------

    text = models.TextField()
    processed_code = models.IntegerField(null=False, default=PROCESSED_PENDING, choices=PROCESSED_CHOICES, db_index=True)
    name = models.TextField()
    language = models.TextField()
    url = models.TextField(db_index=True)
    date_published = models.DateField()
    type = models.TextField()

    last_sayit_import = models.DateTimeField(blank=True, null=True)
    sayit_section = models.ForeignKey(
        Section, blank=True, null=True, on_delete=models.PROTECT,
        help_text='Associated Sayit section object, if imported',
        )

    # For answer that we fetch from the PMG API, we should store the
    # API URL; we also set it if we discover that an answer originally
    # from the original scraper is (should be!) the same as one from
    # the PMG API.
    pmg_api_url = models.URLField(max_length=1000, blank=True, null=True)

    class Meta:
        unique_together = (
            ('oral_number', 'house', 'year'),
            ('written_number', 'house', 'year'),
            ('president_number', 'house', 'year'),
            ('dp_number', 'house', 'year'),
            )

        # FIXME - When we have Django 1.5 we can have these indices...
        # index_together = (
        #     ('oral_number', 'house', 'year'),
        #     ('written_number', 'house', 'year'),
        #     )

class QuestionPaper(models.Model):
    """Models a group of questions.

    Questions are published in batches, and each batch contains
    some metadata. This is the place to store that metadata.
    """
    # Metadata from Questions start url table
    document_name = models.TextField(max_length=32)
    date_published = models.DateField()
    house = models.CharField(max_length=64)
    language = models.CharField(max_length=16)
    document_number = models.IntegerField()
    source_url = models.URLField(max_length=1000)

    # Body metadata from inside the question paper file
    # Question papers are by unique year/issue number/house
    year = models.IntegerField()
    issue_number = models.IntegerField() # within year.
    parliament_number = models.IntegerField()
    session_number = models.IntegerField() # Unique within parliament
    text = models.TextField()

    class Meta:
        unique_together = ('year', 'issue_number', 'house', 'parliament_number')
        # index_together = ('year', 'issue_number', 'house', 'parliament_number')

int_to_text = {
    1: 'FIRST',
    2: 'SECOND',
    3: 'THIRD',
    4: 'FOURTH',
    5: 'FIFTH',
    6: 'SIXTH',
    7: 'SEVENTH',
    8: 'EIGHTH',
    9: 'NINTH',
    10: 'TENTH',
    }

class Question(models.Model):
    paper = models.ForeignKey(
        QuestionPaper,
        null=True, # FIXME - eventually, this should not be nullable.
        on_delete=models.SET_NULL,
        )
    answer = models.ForeignKey(
        Answer,
        null=True,
        on_delete=models.CASCADE,
        related_name='question',
        )


    # number1 - order questions published
    # Strts at 1 for calendar year, separate sequences for oral, written for both NA and NCOP

    # Questions for written answer and questions for oral answer both have
    # sequence numbers. It looks like these are probably the order the questions
    # were asked in. The sequences are unique for each house for written/oral and
    # restart on 1 each year.

    # At least one of these four numbers should be non-null, and it's possible
    # for more than one to be non-null if a question is transferred from oral to written
    # or vice-versa.
    written_number = models.IntegerField(null=True, db_index=True)
    oral_number = models.IntegerField(null=True, db_index=True)

    # The president and vice president get their own question number sequences for
    # oral questions.
    president_number = models.IntegerField(null=True, db_index=True)
    dp_number = models.IntegerField(null=True, db_index=True)

    # Questions are also referred to by an identifier of the form
    # [NC][OW]\d+[AEX]
    # The meaning of the parts of this identifier is as follows:
    #  - [NC] - tells you the house the question was asked in. See 'house' below.
    #  - [OW] - tells you whether the question is for oral or written answer.
    #           Questions can sometimes be transferred between being oral or
    #           written. When this happens, they may be referred to by the new
    #           identifier with everything the same except the O/W.
    #  - \d+  - (number below) Every question to a particular house in a
    #           particular year gets given another number. This number doesn't
    #           change when the question is translated or has [OW] changed.
    #  - [AEX]- Afrikaans/English/Xhosa. The language the question is currently
    #           being displayed in. Translations of the question will have a
    #           different [AEX] in the identifier.

    # Note that we also store the number, house, and answer_type separately.
    identifier = models.CharField(max_length=10, db_index=True)

    # From the identifier discussed above.
    id_number = models.IntegerField(db_index=True)

    # This is in the identifier above. It should correspond to the house
    # on the referenced QuestionPaper.
    house = models.CharField(max_length=1, choices=house_choices, db_index=True)

    answer_type = models.CharField(
        max_length=1,
        choices=(
            ('O', 'Oral Answer'),
            ('W', 'Written Answer'),
            )
        )

    # Date the question was asked on. Not to be confused with the date the
    # question was published, which is date_published on the QuestionPaper.
    date = models.DateField()

    # This should always be the year from the date above, but is worth
    # storing separately so that we can easily have uniqueness constraints
    # on it.
    year = models.IntegerField(db_index=True)

    # FIXME - is this useful to store/easy to get?
    date_transferred = models.DateField(null=True)

    # FIXME - was this the title for the question asker?
    # title = models.TextField()

    # The actual text of the question.
    question = models.TextField()

    # Text of the person the question is asked of
    questionto = models.TextField()

    # Is the question a translation of one originally asked in another language.
    # Currently we are only storing questions in English.
    translated = models.BooleanField(default=None)

    # oral/written number, asker and askee as as string, for example:
    # '144. Mr D B Feldman (COPE-Gauteng) to ask the Minister of Defence and Military Veterans:'
    # '152. Mr D A Worth (DA-FS) to ask the Minister of Defence and Military Veterans:'
    # '254. Mr R A Lees (DA-KZN) to ask the Minister of Rural Development and Land Reform:'
    intro = models.TextField()

    # Name of the person asking the question.
    askedby = models.TextField()

    last_sayit_import = models.DateTimeField(blank=True, null=True)
    sayit_section = models.ForeignKey(
        Section, blank=True, null=True, on_delete=models.PROTECT,
        help_text='Associated Sayit section object, if imported',
        )

    # For questions that we fetch from the PMG API, we should store
    # the API URL and the speaker's People's Aseembly URL:
    pmg_api_url = models.URLField(max_length=1000, blank=True, null=True)
    pmg_api_member_pa_url = models.URLField(
        max_length=1000, blank=True, null=True)
    pmg_api_source_file_url = models.URLField(
        max_length=1000, blank=True, null=True)

    class Meta:
        unique_together = (
            ('written_number', 'house', 'year'),
            ('oral_number', 'house', 'year'),
            ('president_number', 'house', 'year'),
            ('dp_number', 'house', 'year'),
            )
        # index_together(
        #     ('written_number', 'house', 'year'),
        #     ('oral_number', 'house', 'year'),
        #     ('id_number', 'house', 'year'),
        #     )

        # FIXME - Other things it would be nice to constrain that will have to
        # be done in postgres directly, I think.
        # 1) At least one of written_number and oral_number must be non-null.

#CREATE TABLE completed_documents (`url` string);
