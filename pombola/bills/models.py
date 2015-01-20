from django.db import models


class Bill(models.Model):
    title = models.CharField(max_length=256)
    source_url = models.URLField(unique=True)
    date = models.DateField()
    parliamentary_session = models.ForeignKey('core.ParliamentarySession')
    sponsor = models.ForeignKey('core.Person', related_name="bills_sponsored")

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('date', )
