# encoding: utf-8
from south.db import db
from south.v2 import SchemaMigration
from south.models import MigrationHistory

from django.contrib.contenttypes.models import ContentType

class AppRemoveMigration(SchemaMigration):

    def forwards(self, orm):

        # Do the deletes in a separate transaction, as database errors when
        # deleting a table that does not exist would cause a transaction to be
        # rolled back
        db.start_transaction()

        ContentType.objects.filter(app_label=self.app_name).delete()

        # Remove the entries from South's tables as we don't want to leave
        # incorrect entries in there.
        MigrationHistory.objects.filter(app_name=self.app_name).delete()

        # Commit the deletes to the various tables.
        db.commit_transaction()

        for table in self.tables:

            # Check to see if this table exists. db.execute will return
            # something like [(n, )] where n is the count(*)
            table_exists = db.execute(
                "SELECT count(*) from pg_tables where tablename = '{0}'".format(table)
            )
            if table_exists and table_exists[0][0]:
                db.delete_table(table)

    def backwards(self, orm):

        # There is no backwards - to create the app tables again add the app
        # back in and letting its migrations do the work.
        pass


    models = {}

    complete_apps = []
