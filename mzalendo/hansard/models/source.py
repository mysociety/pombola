from django.db import models

class Source(models.Model):
    """
    Sources of the hansard transcripts
    
    For example a PDF transcript.
    """

    name           = models.CharField(max_length=200, unique=True)
    date           = models.DateField()
    url            = models.URLField()
    last_processed = models.DateField(blank=True, null=True)

    class Meta:
        app_label = 'hansard'
        ordering = [ '-date', 'name' ]

    def __unicode__(self):
        return self.name
            
