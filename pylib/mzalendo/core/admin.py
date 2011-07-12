from django.contrib import admin
from mzalendo.core import models
from django.core.urlresolvers import reverse

def create_admin_link_for(obj, link_text):
    url = reverse(
        'admin:%s_%s_change' % ( obj._meta.app_label, obj._meta.module_name),
        args=[obj.id]
    )
    return u'<a href="%s">%s</a>' % ( url, link_text )

class PositionAdmin(admin.ModelAdmin):
    list_display  = [ 'id', 'show_person', 'show_organisation', 'title', 'start_date', 'end_date' ]
    search_fields = ['person__first_name', 'person__last_name', 'organisation__name' ]
    
    def show_person(self, obj):
        return create_admin_link_for( obj.person, obj.person.name() )
    show_person.allow_tags = True
    
    def show_organisation(self, obj):
        return create_admin_link_for(obj.organisation, obj.organisation.name)
    show_organisation.allow_tags = True


class PositionInlineAdmin(admin.TabularInline):
    model      = models.Position
    extra      = 0
    can_delete = False
    fields     = [ 'person', 'organisation', 'title', 'start_date', 'end_date' ]


class PersonAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("first_name","last_name")}
    inlines       = [ PositionInlineAdmin ]
    list_display  = [ 'slug', 'name', 'date_of_birth' ]
    search_fields = ['first_name', 'last_name']

class PlaceAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display  = [ 'slug', 'name', 'kind', 'show_organisation' ]
    list_filter   = [ 'kind' ]
    search_fields = [ 'name', 'organisation__name' ]

    def show_organisation(self, obj):
        if obj.organisation:
            return create_admin_link_for(obj.organisation, obj.organisation.name)
        else:
            return '-'
    show_organisation.allow_tags = True


class PlaceInlineAdmin(admin.TabularInline):
    model      = models.Place
    extra      = 0
    can_delete = False
    fields     = [ 'name', 'slug', 'kind' ]


class OrganisationAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    inlines       = [ PlaceInlineAdmin, PositionInlineAdmin ]
    list_display  = [ 'slug', 'name', 'kind', ]
    list_filter   = [ 'kind', ]
    search_fields = [ 'name' ]

class OrganisationKindAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = [ 'name' ]

class PlaceKindAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = [ 'name' ]

class PositionTitleAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = [ 'name' ]


# Add these to the admin
admin.site.register( models.Organisation,     OrganisationAdmin     )
admin.site.register( models.OrganisationKind, OrganisationKindAdmin )
admin.site.register( models.Person,           PersonAdmin           )
admin.site.register( models.Place,            PlaceAdmin            )
admin.site.register( models.PlaceKind,        PlaceKindAdmin        )
admin.site.register( models.Position,         PositionAdmin         )
admin.site.register( models.PositionTitle,    PositionTitleAdmin    )
