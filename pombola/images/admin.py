from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from sorl.thumbnail import get_thumbnail
from sorl.thumbnail.admin import AdminImageMixin

from pombola.images import models


@admin.register(models.Image)
class ImageAdmin(AdminImageMixin, admin.ModelAdmin):
    list_display = [ 'thumbnail', 'content_object', 'is_primary', 'source',  ]
    search_fields = ['person__legal_name', 'id', 'source']

    def thumbnail(self, obj):
        if obj.image:
            im = get_thumbnail(obj.image, '100x100')
            return '<img src="%s" />' % ( im.url )
        else:
            return "NO IMAGE FOUND"
    thumbnail.allow_tags = True


class ImageAdminInline(AdminImageMixin, GenericTabularInline):
    model        = models.Image
    extra        = 0
    can_delete   = True

