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
           {'fields': ('content_type', 'object_id', 'submit_date', 'ip_address', 'status', 'flag_count')}
        ),
     )

    list_display = ('user', 'title', 'comment', 'content_object', 'status', 'flag_count', 'submit_date')
    list_display_links = ('title',)
    list_editable = ('status',)
    list_filter = ('submit_date', 'status')
    date_hierarchy = 'submit_date'
    ordering = ('-submit_date',)
    raw_id_fields = ('user',)
    search_fields = ('comment', 'user__username', 'ip_address')
    actions = ["approve_comments", "reject_comments"]

    def get_actions(self, request):
        actions = super(CommentAdmin, self).get_actions(request)
        # Only superusers should be able to delete the comments from the DB.
        if not request.user.is_superuser and 'delete_selected' in actions:
            actions.pop('delete_selected')
        if not request.user.has_perm('comments.can_moderate'):
            if 'approve_comments' in actions:
                actions.pop('approve_comments')
            if 'remove_comments' in actions:
                actions.pop('reject_comments')
        return actions
    
    def approve_comments(self, request, queryset):
        for comment in queryset: comment.approve()
        self.message_user(request, "Approved the comments")
    approve_comments.short_description = _("Approve selected comments")
    
    def reject_comments(self, request, queryset):
        queryset.update(status="rejected")
        self.message_user(request, "Rejected the comments")
    reject_comments.short_description = _("Reject selected comments")


class CommentFlagAdmin(admin.ModelAdmin):
    list_display  = [ 'id', 'user', 'comment', 'flag_date', ]
    raw_id_fields = ('user', 'comment', )


admin.site.register(Comment,     CommentAdmin)
admin.site.register(CommentFlag, CommentFlagAdmin)
