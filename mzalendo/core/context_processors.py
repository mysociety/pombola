from django.conf import settings
import logging

def add_settings( request ):
    """Add some selected settings values to the context"""
    return {
        'settings': {            
            'STAGING':                      settings.STAGING,
            'STATIC_GENERATION_NUMBER':     settings.STATIC_GENERATION_NUMBER,
            'GOOGLE_ANALYTICS_ACCOUNT':     settings.GOOGLE_ANALYTICS_ACCOUNT,
            'FACEBOOK_APP_ID':              settings.FACEBOOK_APP_ID,
            'SOCIAL_AUTH_ENABLED_BACKENDS': settings.SOCIAL_AUTH_ENABLED_BACKENDS,
            'POLLDADDY_WIDGET_ID':          settings.POLLDADDY_WIDGET_ID,
            'DISQUS_SHORTNAME':             settings.DISQUS_SHORTNAME,
            'TWITTER_ACCOUNT_NAME':         settings.TWITTER_ACCOUNT_NAME,
            'BLOG_RSS_FEED':                settings.BLOG_RSS_FEED,
            'ENABLED_FEATURES':             settings.ENABLED_FEATURES,
            'MAP_BOUNDING_BOX_NORTH':       settings.MAP_BOUNDING_BOX_NORTH,
            'MAP_BOUNDING_BOX_EAST':        settings.MAP_BOUNDING_BOX_EAST,
            'MAP_BOUNDING_BOX_SOUTH':       settings.MAP_BOUNDING_BOX_SOUTH,
            'MAP_BOUNDING_BOX_WEST':        settings.MAP_BOUNDING_BOX_WEST,
        }        
    }
