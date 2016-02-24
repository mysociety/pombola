from django.db import models
from django.core.urlresolvers import reverse

class HansardModelBase(models.Model):
    
    def get_admin_url(self):
        url = reverse(
            'admin:%s_%s_change' % ( self._meta.app_label, self._meta.model_name),
            args=[self.id]
        )
        return url
    

    class Meta:
       abstract = True      
