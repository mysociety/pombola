from django.contrib import admin
import models 

from pombola.slug_helpers.admin import StricterSlugFieldMixin

class QuizAdmin(StricterSlugFieldMixin, admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}

class StatementAdmin(admin.ModelAdmin):
    pass

class PartyAdmin(admin.ModelAdmin):
    pass

class StanceAdmin(admin.ModelAdmin):
    pass

class SubmissionAdmin(admin.ModelAdmin):
    pass

class AnswerAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.Quiz, QuizAdmin)
admin.site.register(models.Statement, StatementAdmin)
admin.site.register(models.Party, PartyAdmin)
admin.site.register(models.Stance, StanceAdmin)
admin.site.register(models.Submission, SubmissionAdmin)
admin.site.register(models.Answer, AnswerAdmin)
