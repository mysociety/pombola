import settings
import logging

def add_settings( request ):
    """Add some selected settings values to the context"""
    return {
        'settings': {            
            'STAGING':                  settings.STAGING,
            'STATIC_GENERATION_NUMBER': settings.STATIC_GENERATION_NUMBER,
            'MAPIT_URL':                settings.MAPIT_URL,
            # 'GOOGLE_ANALYTICS_ACCOUNT': settings.GOOGLE_ANALYTICS_ACCOUNT,
        }        
    }
