import datetime

from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation
)
from django.contrib.contenttypes.models import ContentType
from django_date_extensions.fields import ApproximateDateField
from django.db import models

import babel.numbers
import decimal


class BudgetSession(models.Model):
    created = models.DateTimeField(auto_now_add=True, default=datetime.datetime.now)
    updated = models.DateTimeField(auto_now=True, default=datetime.datetime.now)

    # A name for this budget sessions
    name = models.CharField(
        max_length=150,
    )

    # Dates this budget session runs for
    date_start = ApproximateDateField(blank=True)
    date_end = ApproximateDateField(blank=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta():
        ordering = ('-date_start', 'name')
        verbose_name_plural = 'budget sessions'

class Budget(models.Model):

    created = models.DateTimeField(auto_now_add=True, default=datetime.datetime.now)
    updated = models.DateTimeField(auto_now=True, default=datetime.datetime.now)

    # link to other objects using the ContentType system
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Who actually handed out this budget?
    organisation = models.CharField(
        max_length=150,
    )

    # A budget has to belong to a budget session
    budget_session = models.ForeignKey(BudgetSession, null=True)

    # A name for this budget.
    name = models.CharField(
        max_length=150,
    )

    # The ISO 4217 code for the currency of the budget
    currency = models.CharField(
        max_length=3,
    )

    # The actual value of this budget
    value = models.IntegerField()

    # A nice formatted value of this budget
    @property
    def formatted_value(self):
        return babel.numbers.format_currency(decimal.Decimal(self.value), self.currency)


    # Every budget can have an external source.
    source_url = models.URLField(blank=True)
    source_name = models.CharField(max_length=200, blank=True)

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.budget_session)

    class Meta():
        ordering = ('-budget_session__date_start', 'budget_session__name', 'name')
        unique_together = ('content_type', 'object_id', 'name', 'budget_session')
        verbose_name_plural = 'budgets'

class BudgetsMixin(models.Model):
    """Mixin to add budget related methods to models"""

    budget_entries = GenericRelation(Budget)

    def budgets(self):
        return self.budget_entries.all()

    def has_budgets(self):
        return self.budgets().exists()

    class Meta:
       abstract = True
