from django.db import models
from django.contrib import comments

class CommentWithTitle(comments.models.Comment):
    """
    Subclass adding titles.
    
    Note: the default comments have two bools that are used to determine what state the comments are in: is_public and is_removed. Using the truth table below you can see that the logic is somewhat silly, and that a list of possible states would have been a much better choice.
    
      meaning      |  is_public |  is_removed
    -------------------------------------------
    not moderated  |  0         |   0
    ?? not used ?? |  0         |   1
    approved       |  1         |   0
    rejected       |  1         |   1

    I don't know if the above are what the Django authors intended. It makes more sense if you think of 'is_public' as 'is_moderated' instead.
    """

    title = models.CharField(max_length=300)
    
    class Meta():
        ordering = ['-submit_date']
        permissions = (
            ("can_post_without_moderation", "Can post comments without moderation"),
        )

class CommentFlag(comments.models.CommentFlag):
    pass

