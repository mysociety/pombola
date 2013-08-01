# encoding: utf-8
from . import AppRemoveMigration


class Migration(AppRemoveMigration):

    app_name = 'registration'
    tables = [
        'registration_registrationprofile',
    ]
