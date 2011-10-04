from django.conf import settings

MARKITUP_PREVIEW_FILTER = getattr(settings, 'MARKITUP_PREVIEW_FILTER',
                                  getattr(settings, 'MARKITUP_FILTER', None))
MARKITUP_AUTO_PREVIEW = getattr(settings, 'MARKITUP_AUTO_PREVIEW', False)
MARKITUP_SET = getattr(settings, 'MARKITUP_SET', 'markitup/sets/default')
MARKITUP_SKIN = getattr(settings, 'MARKITUP_SKIN', 'markitup/skins/simple')
JQUERY_URL = getattr(
    settings, 'JQUERY_URL',
    'http://ajax.googleapis.com/ajax/libs/jquery/1.6/jquery.min.js')
