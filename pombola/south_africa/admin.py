from django.contrib import admin

from pombola.south_africa import models

@admin.register(models.AttendanceForOrganisationToggle)
class AttendanceForOrganisationToggleAdmin(admin.ModelAdmin):
    actions = None

    fields = ['name', 'show_attendance']
    readonly_fields = ['name']
    list_display = ['slug', 'name', 'kind', 'show_attendance']
    search_fields = ['name']

    def get_queryset(self, request):
        """Only allow attendance to be toggled for parties."""
        qs = super(AttendanceForOrganisationToggleAdmin, self).get_queryset(request)
        return qs.filter(kind__slug='party')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False