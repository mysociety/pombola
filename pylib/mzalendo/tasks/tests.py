"""
Test the tasks
"""

from django.test import TestCase
from django.contrib.sites.models import Site
from models import Task

class TaskTest(TestCase):

    def setUp(self):
        # use the site object to run tests against
        self.test_object = Site.objects.all()[0]


    def test_list_creation_and_deletion(self):
        """
        Test that tasks are created and deleted correctly by being given an object and a list
        """

        initial_list  = [ 'task-code-1', 'task-code-2' ]
        modified_list = [ 'task-code-1', 'task-code-3' ]

        # check that there are none at the start
        self.assertEqual( Task.objects.count(), 0 )

        # create a couple of tasks
        Task.update_for_object(
            self.test_object,
            initial_list
        )
        self.assertItemsEqual(
            [ i.task_code for i in Task.objects_for( self.test_object) ],
            initial_list,
        )
        
        # modify one of the tasks
        for task in Task.objects_for( self.test_object ).filter(task_code='task-code-1'):
            task.note = "test notes"
            task.save()
    
        # run again - this time with a new task
        Task.update_for_object(
            self.test_object,
            modified_list
        )
        self.assertItemsEqual(
            [ i.task_code for i in Task.objects_for( self.test_object) ],
            modified_list,
        )

        # check previously modified task unchanged
        for task in Task.objects_for( self.test_object ).filter(task_code='task-code-1'):
            self.assertEqual( task.note, "test notes" )
    
        # run again - with empty list
        Task.update_for_object(
            self.test_object,
            []
        )
        self.assertItemsEqual(
            [ i.task_code for i in Task.objects_for( self.test_object) ],
            [],
        )
        
        # check that all tasks are now deleted
        self.assertEqual( Task.objects.count(), 0 )

