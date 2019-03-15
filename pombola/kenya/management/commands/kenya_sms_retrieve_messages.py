from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from pombola.sms.api import APIClient
from pombola.sms.models import Message

class Command(BaseCommand):
    help = 'Retrieves the latest messages from the SMS API'

    def add_arguments(self, parser):
        parser.add_argument('--start-date', help='Optional start date to get messages from. Example: 2018-10-01')
        parser.add_argument('--end-date', help='Optional end date to get messages to. Example: 2019-03-01')

    def handle(self, *args, **options):
        api_client = APIClient(
            base_url=settings.KENYA_SMS_API_URL,
            api_key=settings.KENYA_SMS_API_KEY
        )
        new_messages = 0
        messages = api_client.get_messages(
            start_date=options['start_date'],
            end_date=options['end_date']
        )
        for message in messages:
            _, created = Message.objects.get_or_create(
                text=message.message,
                msisdn=message.msisdn,
                datetime=message.datetime
            )
            if created:
                new_messages += 1
        self.stdout.write("Created {} new message(s)".format(new_messages))
