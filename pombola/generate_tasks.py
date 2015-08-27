#!/usr/bin/env python

"""
Go through all models that are task related and check that all tasks have been
generated.
"""

from pombola.core import models
from pombola.tasks.models import Task

task_related_models = [models.PopoloPerson, models.Contact]

for m in task_related_models:
    for obj in m.objects.all():
        Task.call_generate_tasks_on( obj )

