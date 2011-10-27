import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core import urlresolvers
from django.db import models
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _

class CommentManager(models.Manager):

    def in_moderation(self):
        """
        QuerySet for all comments currently in the moderation queue.
        """
        return self.get_query_set().filter(status='unmoderated')

    def for_model(self, model):
        """
        QuerySet for all comments for a particular model (either an instance or
        a class).
        """
        ct = ContentType.objects.get_for_model(model)
        qs = self.get_query_set().filter(content_type=ct)
        if isinstance(model, models.Model):
            qs = qs.filter(object_pk=force_unicode(model._get_pk_val()))
        return qs

COMMENT_MAX_LENGTH = getattr(settings,'COMMENT_MAX_LENGTH',3000)

class Comment(models.Model):
    """
    A user comment about some object.
    """

    # Content-object field
    content_type   = models.ForeignKey(ContentType,
            verbose_name=_('content type'),
            related_name="content_type_set_for_%(class)s")
    object_pk      = models.TextField(_('object ID'))
    content_object = generic.GenericForeignKey(ct_field="content_type", fk_field="object_pk")

    user = models.ForeignKey(User, verbose_name=_('user'), related_name="%(class)s_comments")

    title = models.CharField(max_length=300)
    comment = models.TextField(_('comment'), max_length=COMMENT_MAX_LENGTH)

    # Metadata about the comment
    submit_date = models.DateTimeField(_('date/time submitted'), default=None)
    ip_address  = models.IPAddressField(_('IP address'), blank=True, null=True)

    # state of this comment
    status = models.CharField(
        max_length = 20,
        default = 'unmoderated',
        choices = (
            ( 'unmoderated', 'Unmoderated' ),
            ( 'approved',    'Approved'    ),
            ( 'rejected',    'Rejected'    ),
        ),
    )

    # Manager
    objects = CommentManager()

    class Meta:
        ordering = ('-submit_date', )
        permissions = [("can_moderate", "Can moderate comments")]
        verbose_name = _('comment')
        verbose_name_plural = _('comments')
        permissions = (
            ("can_post_without_moderation", "Can post comments without moderation"),
        )
        
    def __unicode__(self):
        return "%s: %s..." % (self.name, self.comment[:50])

    def get_content_object_url(self):
        """
        Get a URL suitable for redirecting to the content object.
        """
        return urlresolvers.reverse(
            "comments-url-redirect",
            args=(self.content_type_id, self.object_pk)
        )

    def save(self, *args, **kwargs):
        if self.submit_date is None:
            self.submit_date = datetime.datetime.now()
            
        # Let other code check that the user is set
        if self.user_id:
            # If user is trusted then approve the comment            
            if self.user.has_perm('comments2.can_post_without_moderation'):
                self.status = 'approved'
        
        super(Comment, self).save(*args, **kwargs)

    def get_absolute_url(self, anchor_pattern="#c%(id)s"):
        return self.get_content_object_url() + (anchor_pattern % self.__dict__)

    def get_as_text(self):
        """
        Return this comment as plain text.  Useful for emails.
        """
        d = {
            'user': self.user or self.name,
            'date': self.submit_date,
            'comment': self.comment,
            'domain': self.site.domain,
            'url': self.get_absolute_url()
        }
        return _('Posted by %(user)s at %(date)s\n\n%(comment)s\n\nhttp://%(domain)s%(url)s') % d


class CommentFlag(models.Model):
    """
    Records a flag on a comment. The flag does not mean anything other than that
    a moderator should look at this comment. If a moderator looks at a comment
    and decides it is ok the flags should be deleted from the database. If the
    comment is then flagged again the moderator should reconsider it. If
    comments keep getting flagged and those flags should be ignored then we'll
    need to add somethin to deal with that.
    """

    user      = models.ForeignKey(User, blank=True, null=True, verbose_name=_('user'), related_name="comment_flags")
    comment   = models.ForeignKey(Comment, verbose_name=_('comment'), related_name="flags")
    flag_date = models.DateTimeField(_('date'), default=None)


    class Meta:
        unique_together = [('user', 'comment')]
        verbose_name = _('comment flag')
        verbose_name_plural = _('comment flags')

    def __unicode__(self):
        return "Flag of comment ID %s by %s" % \
            (self.flag, self.comment_id, self.user.username)

    def save(self, *args, **kwargs):
        if self.flag_date is None:
            self.flag_date = datetime.datetime.now()
        super(CommentFlag, self).save(*args, **kwargs)
