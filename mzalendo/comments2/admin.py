from django.contrib import admin
from comments2.models import Comment, CommentFlag
from django.utils.translation import ugettext_lazy as _, ungettext
# from django.contrib.comments.views.moderation import perform_flag, perform_approve, perform_delete

class CommentAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('Content'),
           {'fields': ('user', 'title', 'comment')}
        ),
        (_('Metadata'),
           {'fields': ('content_type', 'object_pk', 'submit_date', 'ip_address', 'status')}
        ),
     )

    list_display = ('content_object', 'submit_date', 'title', 'status')
    list_filter = ('submit_date', 'status')
    date_hierarchy = 'submit_date'
    ordering = ('-submit_date',)
    raw_id_fields = ('user',)
    search_fields = ('comment', 'user__username', 'ip_address')
    # actions = ["flag_comments", "approve_comments", "remove_comments"]

    # def get_actions(self, request):
    #     actions = super(CommentsAdmin, self).get_actions(request)
    #     # Only superusers should be able to delete the comments from the DB.
    #     if not request.user.is_superuser and 'delete_selected' in actions:
    #         actions.pop('delete_selected')
    #     if not request.user.has_perm('comments.can_moderate'):
    #         if 'approve_comments' in actions:
    #             actions.pop('approve_comments')
    #         if 'remove_comments' in actions:
    #             actions.pop('remove_comments')
    #     return actions
    # 
    # def flag_comments(self, request, queryset):
    #     self._bulk_flag(request, queryset, perform_flag,
    #                     lambda n: ungettext('flagged', 'flagged', n))
    # flag_comments.short_description = _("Flag selected comments")
    # 
    # def approve_comments(self, request, queryset):
    #     self._bulk_flag(request, queryset, perform_approve,
    #                     lambda n: ungettext('approved', 'approved', n))
    # approve_comments.short_description = _("Approve selected comments")
    # 
    # def remove_comments(self, request, queryset):
    #     self._bulk_flag(request, queryset, perform_delete,
    #                     lambda n: ungettext('removed', 'removed', n))
    # remove_comments.short_description = _("Remove selected comments")
    # 
    # def _bulk_flag(self, request, queryset, action, done_message):
    #     """
    #     Flag, approve, or remove some comments from an admin action. Actually
    #     calls the `action` argument to perform the heavy lifting.
    #     """
    #     n_comments = 0
    #     for comment in queryset:
    #         action(request, comment)
    #         n_comments += 1
    # 
    #     msg = ungettext(u'1 comment was successfully %(action)s.',
    #                     u'%(count)s comments were successfully %(action)s.',
    #                     n_comments)
    #     self.message_user(request, msg % {'count': n_comments, 'action': done_message(n_comments)})

class CommentFlagAdmin(admin.ModelAdmin):
    list_display  = [ 'id', 'user', 'comment', 'flag_date', ]
    raw_id_fields = ('user', 'comment', )


admin.site.register(Comment,     CommentAdmin)
admin.site.register(CommentFlag, CommentFlagAdmin)
