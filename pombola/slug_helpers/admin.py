import re

from django.contrib.gis import db
from django.core.exceptions import ValidationError

def stricter_validate_slug(slug):
    if not re.match(r'^[-a-z0-9_]+$', slug):
        raise ValidationError(
            "Enter a valid 'slug' consisting of only lowercase letters, numbers, underscores or hyphens.")
    return True


class StricterSlugFieldMixin(object):
    formfield_overrides = {
        db.models.SlugField: {
            'validators': [stricter_validate_slug]
        }
    }
