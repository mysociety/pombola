from django.contrib import admin

from django.contrib.comments.admin import CommentsAdmin
from django.contrib.comments.models import CommentFlag
from mz_comments.models import CommentWithTitle

class CommentWithTitleAdmin(CommentsAdmin):
    pass

class CommentFlagAdmin(admin.ModelAdmin):
    list_display  = [ 'id', 'user', 'comment', 'flag_date', ]

    # Should add more stuff here - like actions. But it might be better to use a
    # more comprehensive comment system that the one that comes with Django.

admin.site.register(CommentWithTitle, CommentWithTitleAdmin)
admin.site.register(CommentFlag,      CommentFlagAdmin)
