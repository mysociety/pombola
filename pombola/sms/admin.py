from django.contrib import admin
from .models import Message, Question


class MessageAdmin(admin.ModelAdmin):
    list_display = ('text', 'msisdn', 'datetime', 'status')
    list_filter = ('status',)
    actions = ['mark_as_accepted', 'mark_as_rejected']
    date_hierarchy = 'datetime'
    readonly_fields = ('text', 'msisdn', 'datetime')

    def mark_as_accepted(self, request, queryset):
        queryset.update(status=Message.ACCEPTED)
    mark_as_accepted.short_description = 'Accept selected messages'

    def mark_as_rejected(self, request, queryset):
        queryset.update(status=Message.REJECTED)
    mark_as_rejected.short_description = 'Reject selected messages'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.disable_action('delete_selected')
admin.site.register(Message, MessageAdmin)


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'created')

admin.site.register(Question, QuestionAdmin)
