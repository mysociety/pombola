# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import DataMigration

class Migration(DataMigration):
 
    def forwards(self, orm):
        db.execute("UPDATE auth_user SET password='bcrypt' || SUBSTR(password, 3) WHERE password LIKE 'bc$%%'")
 
    def backwards(self, orm):
        db.execute("UPDATE auth_user SET password='bc' || SUBSTR(password, 7) WHERE password LIKE 'bcrypt$%%'")
