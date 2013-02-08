from django.contrib import admin
import models 

class QuizAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["legal_name"]}

admin.site.register(models.Quiz, QuizAdmin)
