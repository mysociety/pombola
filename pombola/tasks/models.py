import datetime

from django.db import models

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models import signals
from django.dispatch import receiver


class TaskCategory(models.Model):
    slug     = models.SlugField(max_length=100, unique=True)
    priority = models.PositiveIntegerField(default=0)


    def __unicode__(self):
        return self.slug


    class Meta:
       ordering = ["-priority", "slug" ]
       verbose_name_plural = "Task categories"


class Task(models.Model):

    # link to other objects using the ContentType system
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    category      = models.ForeignKey(TaskCategory)

    created       = models.DateTimeField(auto_now_add=True)
    defer_until   = models.DateTimeField(auto_now_add=True)
    priority      = models.PositiveIntegerField() # defaulted in overloaded .save() method
    attempt_count = models.PositiveIntegerField(default=0)
    
    log  = models.TextField(blank=True)
    note = models.TextField(blank=True)

    def clean(self):
        """If needed get the priority from the category"""
        if self.priority is None:
            self.priority = self.category.priority


    def __unicode__(self):
        return "%s for %s" % ( self.category.slug, self.content_object )


    @classmethod
    def objects_for(cls, obj):
        """Return qs for all tasks for the given object"""

        # not all primary keys are ints. Check that we can represent them as such

        raw_id = obj.pk
        if str(raw_id).isdigit():
            id = int(raw_id)
        else:
            return cls.objects.none()

        return cls.objects.filter(
            content_type = ContentType.objects.get_for_model(obj),
            object_id    = id,
        )


    @classmethod
    def objects_to_do(cls):
        """Return qs for all tasks that need to be done"""
        return (
            cls
            .objects
            .filter( defer_until__lte=datetime.datetime.now() )
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
        slug_list = obj.generate_tasks()
        cls.update_for_object( obj, slug_list )
        return True


    @classmethod
    def update_for_object(cls, obj, slug_list):
        """Create specified tasks for this objects, delete ones that are missing"""

        # get the details needed to create a generic
        content_type = ContentType.objects.get_for_model(obj)
        object_id    = obj.pk

        # note all tasks seen so we can delete redundant existing ones
        seen_tasks = []

        # check that we have tasks for all codes requested
        for slug in slug_list:

            category, created = TaskCategory.objects.get_or_create(slug=slug)

            task, created = Task.objects.get_or_create(
                content_type = content_type,
                object_id    = object_id,
                category     = category,
                defaults = {
                    'priority': category.priority,
                },
            )
            seen_tasks.append( slug )

        # go through all tasks in db and delete redundant ones
        for task in cls.objects_for(obj):
            if task.category.slug in seen_tasks: continue
            task.delete()

        pass


    def add_to_log(self, msg):
        """append msg to the log entry"""
        current_log = self.log
        if current_log:
            self.log = current_log + "\n" + msg
        else:
            self.log = msg
        return True
    
    def defer_by_days(self, days):
        """Change the defer_until to now + days"""
        new_defer_until = datetime.datetime.now() + datetime.timedelta( days=days )
        self.defer_until = new_defer_until
        return True
        
    def defer_briefly_if_needed(self):
        """If task's defer_until to now + 20 minutes (if needed)"""
        new_defer_until = datetime.datetime.now() + datetime.timedelta( minutes=20 )
        if self.defer_until < new_defer_until:
            self.defer_until = new_defer_until
            self.save()
        return True

    class Meta:
       ordering = ["-priority", "attempt_count", "defer_until" ]
       # FIXME - add http://docs.djangoproject.com/en/dev/ref/models/options/#unique-together


# NOTE - these two signal catchers may prove to be performance bottlenecks in
# future. If so the check to see if there is a generate_tasks method might be
# better replaced with something else...

@receiver( signals.post_delete )
def delete_related_tasks(sender, instance, **kwargs):
    Task.objects_for(instance).delete();


@receiver( signals.post_save )
def post_save_call_generate_tasks(sender, instance, **kwargs):
    return Task.call_generate_tasks_on_if_possible( instance )


