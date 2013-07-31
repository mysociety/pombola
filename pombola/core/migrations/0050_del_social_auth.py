# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.db.utils import DatabaseError

from django.contrib.contenttypes.models import ContentType

class Migration(SchemaMigration):

    def forwards(self, orm):

        # delete entries in a separate transaction.
        db.start_transaction()
        ContentType.objects.filter(app_label='social_auth').delete()
        db.commit_transaction()

        tables_to_delete = [
            'social_auth_association',
            'social_auth_nonce',
            'social_auth_usersocialauth',
        ]

        try:
            for table in tables_to_delete:
                db.delete_table(table)
        except DatabaseError:
            # table does not exist to delete, probably because the database was
            # not created at a time when the user_profile app was still in use.
            pass

    def backwards(self, orm):

        # There is no backwards - to create the social_auth tables again add the app
        # back in and let its migrations do the work.
        pass


    models = {}

    complete_apps = ['social_auth']
