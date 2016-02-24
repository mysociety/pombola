from django.contrib import admin

from pombola.bills import models

@admin.register(models.Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'sponsor']
    search_fields = ['title', 'sponsor__name', 'source_url']
