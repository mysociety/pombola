"""
Test the tasks
"""

from django.test import TestCase
from django.contrib.sites.models import Site
from models import TaskCategory, Task


class TaskTest(TestCase):

    def setUp(self):
        # use the site object to run tests against
        self.test_object = Site.objects.all()[0]

        self.high_priority_category = TaskCategory(
            slug     = "high-priority",
            priority = 10,
        )
        self.high_priority_category.save()

        self.medium_priority_category = TaskCategory(
            slug     = "medium-priority",
            priority = 6,
        )
        self.medium_priority_category.save()

        self.low_priority_category = TaskCategory(
            slug     = "low-priority",
            priority = 3,
        )
        self.low_priority_category.save()


    def test_priority_default(self):
        """Test that the priority is taken from category if needed"""

        # create task with explicit priority
        explicit_task = Task(
            category = self.high_priority_category,
            priority = 5,
        )
        explicit_task.clean()
        self.assertEqual( explicit_task.priority, 5 )

        # create task with default priority
        defaulted_task = Task(
            category = self.high_priority_category,
        )
        defaulted_task.clean()
        self.assertEqual( defaulted_task.priority, self.high_priority_category.priority )


    def test_list_creation_and_deletion(self):
        """
        Test that tasks are created and deleted correctly by being given an object and a list
        """

        initial_list  = [ self.high_priority_category.slug, self.medium_priority_category.slug ]
        modified_list = [ self.high_priority_category.slug, self.low_priority_category.slug ]

        # check that there are none at the start
        self.assertEqual( Task.objects.count(), 0 )

        # create a couple of tasks
        Task.update_for_object(
            self.test_object,
            initial_list
        )
        self.assertItemsEqual(
            [ i.category.slug for i in Task.objects_for( self.test_object) ],
            initial_list,
        )
        
        # modify one of the tasks
        for task in Task.objects_for( self.test_object ).filter(category__slug='task-code-1'):
            task.note = "test notes"
            task.save()
    
        # run again - this time with a new task
        Task.update_for_object(
            self.test_object,
            modified_list
        )
        self.assertItemsEqual(
            [ i.category.slug for i in Task.objects_for( self.test_object) ],
            modified_list,
        )

        # check previously modified task unchanged
        for task in Task.objects_for( self.test_object ).filter(category__slug='task-code-1'):
            self.assertEqual( task.note, "test notes" )
    
        # run again - with empty list
        Task.update_for_object(
            self.test_object,
            []
        )
        self.assertItemsEqual(
            [ i.category.slug for i in Task.objects_for( self.test_object) ],
            [],
        )
        
        # check that all tasks are now deleted
        self.assertEqual( Task.objects.count(), 0 )


    def test_object_deletion(self):
        """
        Test that tasks are created and deleted correctly by being given an object and a list
        """
        
        # test objects
        normal_object    = self.test_object
        deletable_object = test_object = Site(name='foo', domain='foo.com')
        deletable_object.save()
        
        # check that there are none at the start
        self.assertEqual( Task.objects.count(), 0 )

        # create a couple of tasks
        for obj in [ normal_object, deletable_object ]:
            Task.update_for_object( obj, ['foo'] )

        # check that a task exists
        self.assertEqual( Task.objects.count(), 2 )
        self.assertEqual( Task.objects_for(deletable_object).count(), 1 )

        test_object.delete()
        
        # check that a task exists
        self.assertEqual( Task.objects.count(), 1 )
        self.assertEqual( Task.objects_for(deletable_object).count(), 0 )


    def test_object_saving(self):
        """
        Check that the post-save hook works
        """
        
        # test objects
        test_object    = self.test_object

        # save the test object and check that it has no effect
        self.assertEqual( Task.objects.count(), 0 )
        test_object.save()
        self.assertEqual( Task.objects.count(), 0 )
        
        # Manually monkey patch site to have a 'generate_tasks' method
        current_site_name = test_object.name
        def generate_tasks(self):
            if self.name == current_site_name:
                return [ 'change-default-name' ]
            return []
        Site.generate_tasks = generate_tasks

        # save the test oject again and check that a task has been created
        test_object.save()
        self.assertEqual( Task.objects.count(), 1 )
        self.assertEqual( Task.objects.all()[0].category.slug, 'change-default-name' )
        
        # change the name and check that the task gets deleted
        test_object.name = 'not the default'
        test_object.save()
        self.assertEqual( Task.objects.count(), 0 )
        
        # tidy up the Site class
        del Site.generate_tasks


    def test_add_to_log(self):
        """test the add_to_log function"""
        task = Task()
        self.assertEqual( task.log, "")

        task.add_to_log("foo")
        self.assertEqual( task.log, "foo")

        task.add_to_log("bar")
        self.assertEqual( task.log, "foo\nbar")

