from django.db import models

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models import signals
from django.dispatch import receiver



class Task(models.Model):

    # link to other objects using the ContentType system
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    task_code     = models.SlugField(max_length=100)

    created       = models.DateTimeField(auto_now_add=True)
    defer_until   = models.DateTimeField(auto_now_add=True)
    attempt_count = models.PositiveIntegerField(default=0)
    
    log  = models.TextField()
    note = models.TextField(blank=True, help_text="publicaly visible, use to clarify contact detail")

    def __unicode__(self):
        return "%s for %s" % ( self.task_code, self.content_object )


    @classmethod
    def objects_for(cls, obj):
        """Return qs for all tasks for the given object"""
        return cls.objects.filter(
            content_type = ContentType.objects.get_for_model(obj),
            object_id    = obj.pk
        )
    
    
    @classmethod
    def call_generate_tasks_on_if_possible(cls, obj):
        """call generate_tasks on the given object and process the results"""
        if hasattr( obj, 'generate_tasks' ):
            return cls.call_generate_tasks_on( obj )
        return False
        

    @classmethod
    def call_generate_tasks_on(cls, obj):
        """call generate_tasks on the given object and process the results"""
        task_code_list = obj.generate_tasks()
        cls.update_for_object( obj, task_code_list )
        return True


    @classmethod
    def update_for_object(cls, obj, task_code_list):
        """Create specified tasks for this objects, delete ones that are missing"""

        # get the details needed to create a generic
        content_type = ContentType.objects.get_for_model(obj)
        object_id    = obj.pk

        # note all tasks seen so we can delete redundant existing ones
        seen_tasks = []

        # check that we have tasks for all codes requested
        for task_code in task_code_list:
            task, created = Task.objects.get_or_create(
                content_type = content_type,
                object_id    = object_id,
                task_code    = task_code,
            )
            seen_tasks.append( task_code )

        # go through all tasks in db and delete redundant ones
        for task in cls.objects_for(obj):
            if task.task_code in seen_tasks: continue
            task.delete()

        pass


    class Meta:
       ordering = ["content_type", "object_id", "task_code", ]      


# NOTE - these two signal catchers may prove to be performance bottlenecks in
# future. If so the check to see if there is a generate_tasks method might be
# better replaced with something else...

@receiver( signals.post_delete )
def delete_related_tasks(sender, instance, **kwargs):
    Task.objects_for(instance).delete();


@receiver( signals.post_save )
def post_save_call_generate_tasks(sender, instance, **kwargs):
    return Task.call_generate_tasks_on_if_possible( instance )


