from django.core.management.base import BaseCommand

from pombola.core.models import Person

class Command(BaseCommand):

    def handle(self, **options):
        help = 'List the paths of primary person images relative to media root'

        for p in Person.objects.filter(hidden=False):
            image_file_field = p.primary_image()
            if not image_file_field:
                continue
            print image_file_field.name
