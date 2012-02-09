from django.contrib import admin
from feedback.models import Feedback

class FeedbackAdmin(admin.ModelAdmin):

    list_display = ('status', 'comment', 'user', 'email', 'url', 'created',)
    list_filter = ('created', 'status')
    date_hierarchy = 'created'
    ordering = ('-created',)
    raw_id_fields = ('user',)
    search_fields = ('comment', 'user__username', 'url', 'email')

admin.site.register( Feedback, FeedbackAdmin )
