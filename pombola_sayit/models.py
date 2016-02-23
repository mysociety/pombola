from django.db import models

from pombola.core.models import Person
from speeches.models import Speaker

from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^instances\.fields\.DNSLabelField"])


class PombolaSayItJoin(models.Model):

    """This model provides a join table between Pombola and SsayIt people"""

    pombola_person = models.OneToOneField(Person, related_name='sayit_link')
    sayit_speaker = models.OneToOneField(Speaker, related_name='pombola_link')
