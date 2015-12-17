from django.core.management.base import NoArgsCommand
from django.contrib.sites.models import Site

from pombola.feedback.models import Feedback


class Command(NoArgsCommand):
    help = 'Report all the feedbac that needs attention'
    args = ''

    def handle_noargs(self, **options):

        pending = Feedback.objects.filter( status='pending' )
        
        
        # If there are no reports to deal with then exit
        if not pending.exists():
            return
        
        subject = "Feedback requires attention - %u pending reports" % pending.count()
        message = "Please visit the admin and process the feedback as needed."
        url = 'http://%s/admin/feedback/feedback/?status=pending' % Site.objects.get_current().domain
        

        print subject
        print
        print message
        print
        print url

