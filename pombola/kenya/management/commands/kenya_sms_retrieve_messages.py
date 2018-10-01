from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from pombola.sms.api import APIClient
from pombola.sms.models import Message

class Command(BaseCommand):
    help = 'Retrieves the latest messages from the SMS API'

    def handle(self, *args, **options):
        api_client = APIClient(
            base_url=settings.KENYA_SMS_API_URL,
            short_code=settings.KENYA_SMS_API_SHORT_CODE
        )
        new_messages = 0
        for message in api_client.latest_messages(limit=50):
            _, created = Message.objects.get_or_create(
                text=message.message(),
                msisdn=message.msisdn(),
                datetime=message.time_in()
            )
            if created:
                new_messages += 1
        self.stdout.write("Created {} new message(s)".format(new_messages))
