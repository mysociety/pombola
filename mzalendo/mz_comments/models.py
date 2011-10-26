from django.db import models
from django.contrib.comments.models import Comment

class CommentWithTitle(Comment):
    title = models.CharField(max_length=300)
    
    class Meta():
        ordering = ['-submit_date']
        permissions = (
            ("can_post_without_moderation", "Can post comments without moderation"),
        )