# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    """An empty migration that simply depends on the core, so that the rest
    are run at the correct time."""
    
    depends_on = (
        ("core", "0024_auto__add_field_positiontitle_requires_place"),
    )

    def forwards(self, orm):
        pass
    
    
    def backwards(self, orm):
        pass
    
    models = {}
    
    complete_apps = ['place_data']
