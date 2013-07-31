# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from south.models import MigrationHistory
from django.db import models
from django.db.utils import DatabaseError

from django.contrib.contenttypes.models import ContentType

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Do the deletes in a separate transaction, as database errors when
        # deleting a table that does not exist would cause a transaction to be
        # rolled back
        db.start_transaction()

        ContentType.objects.filter(app_label='user_profile').delete()

        # Remove the entries from South's tables as we don't want to leave
        # incorrect entries in there.
        MigrationHistory.objects.filter(app_name='user_profile').delete()

        # Commit the deletes to the various tables.
        db.commit_transaction()

        try:
            db.delete_table('user_profile_userprofile')
        except DatabaseError:
            # table does not exist to delete, probably because the database was
            # not created at a time when the user_profile app was still in use.
            pass 


    def backwards(self, orm):

        # There is no backwards - to create the user_profile tables again add the app
        # back in and letting its migrations do the work.
        pass


    models = {}

    complete_apps = ['user_profile']
