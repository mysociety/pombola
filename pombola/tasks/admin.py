import datetime

from django.conf.urls import patterns
from django.contrib import admin
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.core.urlresolvers import reverse
from django.shortcuts  import render_to_response, redirect
from django.template   import RequestContext

import models

from pombola.slug_helpers.admin import StricterSlugFieldMixin


def create_admin_url_for(obj):
    return reverse(
        'admin:%s_%s_change' % ( obj._meta.app_label, obj._meta.module_name),
        args=[obj.id]
    )

def create_admin_link_for(obj, link_text):
    url = create_admin_url_for( obj )
    return u'<a href="%s">%s</a>' % ( url, link_text )


@admin.register(models.Task)
class TaskAdmin(admin.ModelAdmin):
    list_display    = [ 'category', 'show_foreign', 'priority', 'attempt_count', 'defer_until', ]
    list_filter     = [ 'category', ]
    readonly_fields = [ 'category' ]
    fields          = [ 'priority', 'note' ]
    
    def show_foreign(self, obj):
        return create_admin_link_for( obj.content_object, unicode(obj.content_object) )
    show_foreign.allow_tags = True

    def get_urls(self):
        urls = super(TaskAdmin, self).get_urls()
        my_urls = patterns('',
            ( r'^do/$',                     self.do_next ),
            ( r'^do/(?P<task_id>[\d+]+)/$', self.do      ),
        )
        return my_urls + urls
        

    @method_decorator(staff_member_required)
    def do(self, request, task_id):
        
        # load the task - if not possible then redirect to do_next
        try:
            task = models.Task.objects.get(id=task_id)
        except models.Task.DoesNotExist:
            return redirect( '/admin/tasks/task/do/' )
        
        # defer by a few minutes if needed
        task.defer_briefly_if_needed()
        
        # values are in days (approximates used)
        deferrals = {
            'one day':      1,
            'one week':     7,            
            'one month':    30,            
            'three months': 90,            
            'six months':   180,            
        }
        deferral_periods = sorted(
            deferrals.keys(),
            cmp=lambda x,y: cmp( deferrals[x], deferrals[y] )
        )

        show_completed_warning = False
        if request.method == 'POST':
            if request.POST.get('task_completed'):
                # task is not completed - if it were we would be here
                show_completed_warning = True
            else:
                task.note = request.POST.get('note', '')
                
                defer_by   = request.POST.get( 'deferral', 'one day' )
                defer_days = deferrals.get(defer_by, 1)
                task.defer_by_days( defer_days )
                task.add_to_log("%s: task deferred %u days by %s" % (datetime.date.today(), defer_days, request.user.username) )
                task.attempt_count = task.attempt_count + 1
                
                task.save()
                
                return redirect( '/admin/tasks/task/do/' )
        


        return render_to_response(
            'admin/tasks/task/do.html',
            {
                'task':             task,
                'related_tasks':    models.Task.objects_for(task.content_object),                
                'deferral_periods': deferral_periods,
                'object_admin_url': create_admin_url_for(task.content_object),
                'show_completed_warning': show_completed_warning,
            },
            context_instance=RequestContext(request)
        )

    @method_decorator(staff_member_required)
    def do_next(self, request):
        tasks_to_do = models.Task.objects_to_do()

        try:
            task = tasks_to_do[0]
            return redirect( '/admin/tasks/task/do/' + str(task.id) + '/' )
        except IndexError:
            return render_to_response(
                'admin/tasks/task/do_next.html',
                {},
                context_instance=RequestContext(request)
            )


@admin.register(models.TaskCategory)
class TaskCategoryAdmin(StricterSlugFieldMixin, admin.ModelAdmin):
    list_display  = [ 'slug', 'priority', ]


# class TaskInlineAdmin(GenericTabularInline):
#     model      = models.Task
#     extra      = 0
#     can_delete = False
#     fields     = [ 'category' ]
