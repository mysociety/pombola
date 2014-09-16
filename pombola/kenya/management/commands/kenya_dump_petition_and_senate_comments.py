import json
from optparse import make_option
import re

from django.core.management.base import NoArgsCommand

from pombola.feedback.models import Feedback

from csv import DictWriter

def unpack_comment(comment_text):
    m = re.search('(?s)^({.*?}) (.*)$', comment_text)
    if not m:
        raise Exception(u"Found a malformed comment: " + comment_text)
    return json.loads(m.group(1)), m.group(2)

class Command(NoArgsCommand):
    help = 'Generate a CSV file with all candiates for generating Google AdWords'

    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        )

    def handle_noargs(self, **options):
        print "in the command..."

        comment_keys = ('user_key', 'g', 'agroup', 'user_key', 'experiment_slug', 'variant', 'via')

        petition_headers = comment_keys + ('name', 'email')
        # Petition signatories from the first two experiments
        for filename, url_path in [
            ('petition-1.csv', '/county-performance/petition'),
            ('petition-2.csv', '/county-performance-2/petition'),
        ]:
            with open(filename, "wb") as f:
                writer = DictWriter(f, petition_headers)
                writer.writeheader()
                for f in Feedback.objects.filter(url__endswith=url_path):
                    data, comment = unpack_comment(f.comment)
                    row_data = data.copy()
                    row_data['name'] = comment
                    row_data['email'] = f.email
                    writer.writerow(row_data)

        senate_headers = comment_keys + ('comment',)
        for filename, url_path in [
            ('senate-1.csv', '/county-performance/senate'),
            ('senate-2.csv', '/county-performance-2/senate'),
        ]:
            with open(filename, "wb") as f:
                writer = DictWriter(f, senate_headers)
                writer.writeheader()
                for f in Feedback.objects.filter(url__endswith=url_path):
                    data, comment = unpack_comment(f.comment)
                    row_data = data.copy()
                    row_data['comment'] = comment
                    writer.writerow(row_data)

