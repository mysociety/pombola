from django.contrib import admin

from pombola.budgets import models

@admin.register(models.Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['content_object', 'name', 'currency', 'value', 'budget_session']
    search_fields = ['organisation__name', 'place__name']

@admin.register(models.BudgetSession)
class BudgetSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'date_start', 'date_end']
    search_fields = ['name']
