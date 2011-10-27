from django.db import models
from django.contrib import comments

class CommentWithTitle(comments.models.Comment):
    title = models.CharField(max_length=300)
    
    class Meta():
        ordering = ['-submit_date']
        permissions = (
            ("can_post_without_moderation", "Can post comments without moderation"),
        )

class CommentFlag(comments.models.CommentFlag):
    pass

