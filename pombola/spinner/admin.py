from django.contrib import admin

from sorl.thumbnail import get_thumbnail
from sorl.thumbnail.admin import AdminImageMixin

from . import models


class SlideAdmin(admin.ModelAdmin):
    list_display = ('id', 'content_object', 'content_type', 'sort_order', 'is_active')
    list_filter = ('is_active', )


class ImageContentAdmin(AdminImageMixin, admin.ModelAdmin):
    list_display = ('thumbnail', 'caption')
    search_fields = ('caption', )

    def thumbnail(self, obj):
        if obj.image:
            im = get_thumbnail(obj.image, '100x100')
            return '<img src="%s" />' % ( im.url )
        else:
            return "NO IMAGE FOUND"
    thumbnail.allow_tags = True


# Add these to the admin
admin.site.register( models.Slide, SlideAdmin)
admin.site.register( models.ImageContent, ImageContentAdmin)
