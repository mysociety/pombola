# This has migration code that can be reused by migrations in other
# Django applications in Pombola.

import sys

def migrate_generic_foreign_key(orm, orm_label, fk_field='object_id'):
    """Update a generic foreign key the new django-popolo core models"""

    model_map = {
        ('core', 'organisation'): ('core', 'popoloorganization'),
        ('core', 'alternativepersonname'): ('core', 'popolopersonothername'),
        ('core', 'person'): ('core', 'popoloperson'),
        ('core', 'position'): ('core', 'popolomembership'),
    }

    model_to_content_type_id = {
        t: orm['contenttypes.ContentType'].objects.get(
            app_label=t[0], model=t[1]).id
        for t in model_map.keys() + model_map.values()
    }

    content_type_id_to_model = {
        v: k for k, v in model_to_content_type_id.items()
        }

    for old_object in orm[orm_label].objects.all():
        old_model = content_type_id_to_model.get(
            old_object.content_type_id)

        if old_model and old_model in model_map:

            new_model = model_map[old_model]
            new_content_type_id = model_to_content_type_id[new_model]

            old_object.content_type_id = new_content_type_id
            setattr(
                old_object,
                fk_field,
                _get_new_object_id(
                    orm, getattr(old_object, fk_field), old_model)
            )

            if getattr(old_object, fk_field) is not None:
                old_object.save()

def _get_new_object_id(orm, old_object_id, old_model):
    """old_model should be a tuple of (app_label, model_name)."""

    try:
        return orm['popolo.Identifier'].objects.get(
            scheme='old_pombola_{}_id'.format(old_model[1]),
            identifier=str(old_object_id),
            ).object_id
    except orm['popolo.Identifier'].DoesNotExist:
        msg = "No Identifer found mapping the old ID ({0}) for the old model {1}"
        print >> sys.stderr, msg.format(old_object_id, old_model)
        print >> sys.stderr, "(It may refer to someone who has been deleted, " \
            "but there's still a stale generic foreign key to them.)"
