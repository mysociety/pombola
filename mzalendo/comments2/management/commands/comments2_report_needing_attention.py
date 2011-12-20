import datetime

from django.core.management.base import NoArgsCommand

from comments2.models import Comment

class Command(NoArgsCommand):
    help = 'Report all the comments that need moderation'
    args = ''

    def handle_noargs(self, **options):

        unmoderated = Comment.objects.in_moderation()
        flagged     = Comment.objects.flagged()
        
        # count the number in each state
        unmoderated_count = unmoderated.count()
        flagged_count     = flagged.count()
        total_count       = unmoderated_count + flagged_count
        
        # If there are no comments to deal with then exit
        if total_count == 0:
            return
        
        subject = "Comments require attention - %u unmoderated and %u flagged" % ( unmoderated_count, flagged_count )
        message = "Please visit the admin and moderate/review the comments as needed."
        
        print subject
        print message
