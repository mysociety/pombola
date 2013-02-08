from django.contrib import admin
import models 

class QuizAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["legal_name"]}

class StatementAdmin(admin.ModelAdmin):
    pass

class PartyAdmin(admin.ModelAdmin):
    pass

class StanceAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.Quiz, QuizAdmin)
admin.site.register(models.Statement, StatementAdmin)
admin.site.register(models.Party, PartyAdmin)
admin.site.register(models.Stance, StanceAdmin)
