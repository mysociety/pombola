from django import forms
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.gis import db
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.html import escape

from ajax_select import make_ajax_form
from ajax_select.admin import AjaxSelectAdmin

from images.admin import ImageAdminInline
from slug_helpers.admin import StricterSlugFieldMixin

from pombola.core import models
from pombola.scorecards import models as scorecard_models

admin.site.register(models.ParliamentarySession)


def create_admin_link_for(obj, link_text):
    return u'<a href="{url}">{link_text}</a>'.format(
        url=obj.get_admin_url(),
        link_text=escape(link_text)
    )


class ContentTypeModelAdmin(admin.ModelAdmin):

    def show_foreign(self, obj):
        if obj.content_object:
            return create_admin_link_for(
                obj.content_object,
                unicode(obj.content_object)
            )
        return ''

    show_foreign.allow_tags = True


@admin.register(models.ContactKind)
class ContactKindAdmin(StricterSlugFieldMixin, admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ['name']


class AlternativePersonNameInlineAdmin(admin.TabularInline):
    model = models.AlternativePersonName
    extra = 0


@admin.register(models.InformationSource)
class InformationSourceAdmin(ContentTypeModelAdmin):
    list_display = ['source', 'show_foreign', 'entered']
    list_filter = ['entered']
    search_fields = ['source']


class InformationSourceInlineAdmin(GenericTabularInline):
    model = models.InformationSource
    extra = 0
    can_delete = False
    fields = ['source', 'note', 'entered']
    formfield_overrides = {
        db.models.TextField: {
            'widget': forms.Textarea(attrs={'rows':2, 'cols':40}),
            },
    }


@admin.register(models.Contact)
class ContactAdmin(ContentTypeModelAdmin):
    list_display = ['kind', 'value', 'show_foreign']
    search_fields = ['value']
    inlines = [InformationSourceInlineAdmin]


class ContactInlineAdmin(GenericTabularInline):
    model = models.Contact
    extra = 0
    can_delete = True
    fields = ['kind', 'value', 'source', 'note', 'preferred']
    formfield_overrides = {
        db.models.TextField: {
            'widget': forms.Textarea(attrs={'rows':2, 'cols':20}),
            },
    }


@admin.register(models.Identifier)
class IdentifierAdmin(ContentTypeModelAdmin):
    list_display = ['scheme', 'identifier', 'show_foreign']
    search_fields = ['identifier']
    inlines = [InformationSourceInlineAdmin]


class IdentifierInlineAdmin(GenericTabularInline):
    model = models.Identifier
    extra = 0
    can_delete = False
    fields = ['scheme', 'identifier']


@admin.register(models.Position)
class PositionAdmin(AjaxSelectAdmin):
    list_display = [
        'id',
        'show_person',
        'show_organisation',
        'show_place',
        'show_title',
        'start_date',
        'end_date',
        ]
    search_fields = ['person__legal_name', 'organisation__name', 'title__name']
    list_filter = ['title__name']
    inlines = [InformationSourceInlineAdmin]
    readonly_fields = ['sorting_start_date', 'sorting_end_date']

    form = make_ajax_form(
        models.Position,
        {
            'organisation': 'organisation_name',
            'place': 'place_name',
            'person': 'person_name',
            'title': 'title_name',
        }
    )

    def show_person(self, obj):
        return create_admin_link_for(obj.person, obj.person.name)
    show_person.allow_tags = True

    def show_organisation(self, obj):
        if obj.organisation:
            return create_admin_link_for(obj.organisation, obj.organisation.name)
        return ''
    show_organisation.allow_tags = True

    def show_place(self, obj):
        return (
            create_admin_link_for(obj.place, obj.place.name)
            if obj.place else "&mdash;"
            )
    show_place.allow_tags = True

    def show_title(self, obj):
        return (
            create_admin_link_for(obj.title, obj.title.name)
            if obj.title else "&mdash;"
            )
    show_title.allow_tags = True


class PositionInlineAdmin(admin.TabularInline):
    model = models.Position
    extra = 3  # do not set to zero as the autocomplete does not work in inlines
    can_delete = True
    fields = [
        'person',
        'organisation',
        'place',
        'title',
        'subtitle',
        'category',
        'start_date',
        'end_date',
        ]
    form = make_ajax_form(
        models.Position,
        {
            'organisation': 'organisation_name',
            'place': 'place_name',
            'person': 'person_name',
            'title': 'title_name',
        },
    )
    ordering = ('-category', 'organisation__name', '-start_date')

    def get_queryset(self, request):
        queryset = super(PositionInlineAdmin, self).get_queryset(request)
        return queryset.select_related('person', 'organisation', 'title')

class ScorecardInlineAdmin(GenericTabularInline):
    model = scorecard_models.Entry
    fields = ('date', 'score', 'disabled')
    readonly_fields = ('date', 'score')
    extra = 0
    can_delete = False


@admin.register(models.Person)
class PersonAdmin(StricterSlugFieldMixin, admin.ModelAdmin):
    prepopulated_fields = {"slug": ["legal_name"]}
    inlines = [
        AlternativePersonNameInlineAdmin,
        PositionInlineAdmin,
        ContactInlineAdmin,
        InformationSourceInlineAdmin,
        ImageAdminInline,
        ScorecardInlineAdmin,
        IdentifierInlineAdmin,
        ]
    list_display = ['slug', 'name', 'date_of_birth']
    list_filter = ['can_be_featured']
    search_fields = ['legal_name']


@admin.register(models.Place)
class PlaceAdmin(StricterSlugFieldMixin, admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ('slug', 'name', 'kind', 'show_organisation')
    list_filter = ('kind',)
    search_fields = ('name', 'organisation__name')
    inlines = (
        InformationSourceInlineAdmin,
        ImageAdminInline,
        ScorecardInlineAdmin,
        IdentifierInlineAdmin,
        )

    def get_field_queryset(self, db, db_field, request):
        if db_field.name == 'parent_place':
            fields = ('kind', 'organisation', 'parliamentary_session')
            return db_field.rel.to.objects.select_related(*fields)
        elif db_field.name == 'organisation':
            return db_field.rel.to.objects.select_related('kind')
        return None

    def get_queryset(self, request):
        return super(PlaceAdmin, self).get_queryset(request) \
            .select_related(
                'kind', 'organisation', 'organisation__kind', 'parliamentary_session')

    def show_organisation(self, obj):
        if obj.organisation:
            return create_admin_link_for(
                obj.organisation, obj.organisation.name)
        else:
            return '-'
    show_organisation.allow_tags = True


class PlaceInlineAdmin(admin.TabularInline):
    model = models.Place
    extra = 0
    can_delete = False
    fields = ['name', 'slug', 'kind']


@admin.register(models.Organisation)
class OrganisationAdmin(StricterSlugFieldMixin, admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    inlines = [
        PlaceInlineAdmin,
        PositionInlineAdmin,
        ContactInlineAdmin,
        InformationSourceInlineAdmin,
        IdentifierInlineAdmin,
        ImageAdminInline,
        ]
    list_display = ['slug', 'name', 'kind']
    list_filter = ['kind']
    search_fields = ['name']
    exclude = ['show_attendance']


@admin.register(models.OrganisationKind)
class OrganisationKindAdmin(StricterSlugFieldMixin, admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']


@admin.register(models.PlaceKind)
class PlaceKindAdmin(StricterSlugFieldMixin, admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ['slug', 'name']
    search_fields = ['name']


@admin.register(models.PositionTitle)
class PositionTitleAdmin(StricterSlugFieldMixin, admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']


@admin.register(LogEntry)
class LogAdmin(admin.ModelAdmin):
    """Create an admin view of the history/log table"""
    list_display = (
        'action_time',
        'user',
        'content_type',
        'change_message',
        'is_addition',
        'is_change',
        'is_deletion',
        )
    list_filter = ['action_time', 'user', 'content_type']
    ordering = ('-action_time',)
    readonly_fields = [
        'user',
        'content_type',
        'object_id',
        'object_repr',
        'action_flag',
        'change_message',
        ]
    date_hierarchy = 'action_time'

    #We don't want people changing this historical record:
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        #returning false causes table to not show up in admin page :-(
        #I guess we have to allow changing for now
        return True
    def has_delete_permission(self, request, obj=None):
        return False
