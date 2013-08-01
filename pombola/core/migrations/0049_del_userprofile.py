# encoding: utf-8
from . import AppRemoveMigration


class Migration(AppRemoveMigration):

    app_name = 'user_profile'
    tables = ['user_profile_userprofile']
