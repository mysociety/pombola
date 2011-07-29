from django.contrib import admin

from django.contrib.comments.admin import CommentsAdmin
from mz_comments.models import CommentWithTitle

class CommentWithTitleAdmin(admin.ModelAdmin):
    pass

# Only register the default admin if the model is the built-in comment model
# (this won't be true if there's a custom comment app).
admin.site.register(CommentWithTitle, CommentWithTitleAdmin)
