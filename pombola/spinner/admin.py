from django.contrib import admin

from sorl.thumbnail import get_thumbnail
from sorl.thumbnail.admin import AdminImageMixin

from . import models


@admin.register(models.Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ('id', 'content_object', 'content_type', 'sort_order', 'is_active')
    list_filter = ('is_active', )


@admin.register(models.ImageContent)
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


@admin.register(models.QuoteContent)
class QuoteContentAdmin(admin.ModelAdmin):
    search_fields = ('quote', 'attribution')
    list_display = ('id', 'quote', 'attribution')
