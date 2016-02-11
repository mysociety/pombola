from django.conf.urls import patterns, include, url

from pombola.south_africa.views import (
    OldSectionRedirect, OldSpeechRedirect,
    SASpeechView, SASectionView,
    SAHansardIndex, SACommitteeIndex, SAQuestionIndex,
    SASpeakerRedirectView)

# We add redirects for the old-style SayIt patterns, so that old
# bookmarks aren't lost. For examples, links to speeches should still
# work, e.g.
#
#  /question/speech/367721
#  /hansard/speech/7606
#  /committee/speech/318055
#     -> http://www.pmg.org.za/report/20131008-auditor-general-key-challenges-in-agriculture-departments-audit-report-2013-minister-in-attendance
#
# (The last one should be a redirect.)  Old-style links to SayIt
# sections should still work too, e.g.:
#
#  /question/59146
#  /hansard/928

urlpatterns = [
    url(r'^committee/(?P<pk>\d+)$', OldSectionRedirect.as_view()),
    url(r'^question/(?P<pk>\d+)$', OldSectionRedirect.as_view()),
    url(r'^hansard/(?P<pk>\d+)$', OldSectionRedirect.as_view()),

    url(r'^committee/speech/(?P<pk>\d+)$', OldSpeechRedirect.as_view()),
    url(r'^question/speech/(?P<pk>\d+)$', OldSpeechRedirect.as_view()),
    url(r'^hansard/speech/(?P<pk>\d+)$', OldSpeechRedirect.as_view()),
]

# Make sure the top level custom indexes work:

urlpatterns += patterns('',
    url(r'^hansard/?$', SAHansardIndex.as_view(), name='section-list-hansard'),
    url(r'^committee-minutes/?$', SACommitteeIndex.as_view(), name='section-list-committee-minutes'),
    url(r'^question/?$', SAQuestionIndex.as_view(), name='section-list-question'),
)

# Anything else unmatched we assume is dealt with by SayIt (which will
# return a 404 if the path is unknown anyway):

fallback_sayit_patterns = patterns('',
    # Exposed endpoint for a speech referred to by a numeric ID:
    url(r'^speech/(?P<pk>\d+)$', SASpeechView.as_view(), name='speech-view'),
    # Fake endpoint to redirect to the right speaker:
    url(r'^speaker/(?P<pk>\d+)$', SASpeakerRedirectView.as_view(), name='speaker-view'),
    # Anything else might be a slug referring to a section:
    url(r'^(?P<full_slug>.+)$', SASectionView.as_view(), name='section-view'),
)

urlpatterns += patterns('',
    url(r'', include(fallback_sayit_patterns, namespace='sayit', app_name='speeches')),
)
