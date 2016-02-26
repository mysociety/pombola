from django.db import models


class BillQuerySet(models.query.QuerySet):
    def recent(self):
        """
        Return the 10 most recent Bills in reverse chronological order
        """
        return self.filter().order_by("-date")[:10]


class Bill(models.Model):
    title = models.CharField(max_length=256)
    source_url = models.URLField(unique=True)

    # Bills become Acts, so allow the act title and source URL to be stored
    act_title = models.CharField(max_length=256, blank=True, null=True)
    act_source_url = models.URLField(unique=True, blank=True, null=True)

    date = models.DateField()
    parliamentary_session = models.ForeignKey('core.ParliamentarySession')
    sponsor = models.ForeignKey('core.Person', related_name="bills_sponsored")

    objects = BillQuerySet.as_manager()

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('date', )
