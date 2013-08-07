# encoding: utf-8
from . import AppRemoveMigration


class Migration(AppRemoveMigration):

    app_name = 'social_auth'
    tables = [
        'social_auth_association',
        'social_auth_nonce',
        'social_auth_usersocialauth',
    ]
