from django.contrib import admin

from pombola.budgets import models

class BudgetAdmin(admin.ModelAdmin):
    list_display = ['content_object', 'name', 'currency', 'value', 'budget_session']
    search_fields = ['organisation__name', 'place__name']

class BudgetSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'date_start', 'date_end']
    search_fields = ['name']

admin.site.register( models.Budget, BudgetAdmin )
admin.site.register( models.BudgetSession, BudgetSessionAdmin )
