from django.contrib import admin

from slug_helpers.admin import StricterSlugFieldMixin

import models


@admin.register(models.Quiz)
class QuizAdmin(StricterSlugFieldMixin, admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}

@admin.register(models.Statement)
class StatementAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Party)
class PartyAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Stance)
class StanceAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Submission)
class SubmissionAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Answer)
class AnswerAdmin(admin.ModelAdmin):
    pass
