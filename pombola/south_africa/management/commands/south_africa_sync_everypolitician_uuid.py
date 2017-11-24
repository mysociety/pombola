from everypolitician import EveryPolitician

from django.core.management.base import BaseCommand

from pombola.core.models import Person


class Command(BaseCommand):
    help = "Sync EveryPolitician UUID to Person's identifiers array"

    def add_arguments(self, parser):
        parser.add_argument('everypolitician_countries_json_git_ref',
                            default='master', nargs='?',
                            help="A git ref from the everypolitician-data repo")

    def handle(self, **options):
        verbose_level = options['verbosity']

        url_template = ('https://cdn.rawgit.com/everypolitician/everypolitician-data/'
                        '{git_ref}/countries.json')

        url = url_template.format(git_ref=options['everypolitician_countries_json_git_ref'])

        ep = EveryPolitician(countries_json_url=url)
        south_africa_assembly = ep.country('South-Africa').legislature('Assembly').popolo()

        id_lookup = {}
        for popolo_person in south_africa_assembly.persons:
            id_lookup[popolo_person.identifier_value('peoples_assembly')] = popolo_person.id

        error_msg = u"No EveryPolitician UUID found for {0.id} {0.name} https://www.pa.org.za/person/{0.slug}/\n"
        for person in Person.objects.filter(hidden=False):
            uuid = id_lookup.get(str(person.id))
            if uuid is None:
                verbose_level > 1 and self.stderr.write(error_msg.format(person))
                continue
            identifier, created = person.identifiers.get_or_create(
                scheme='everypolitician',
                identifier=uuid,
            )
            if verbose_level > 0:
                if created:
                    msg = u"Created new identifier for {name}: {identifier}"
                else:
                    msg = u"Existing identifier found for {name}: {identifier}"
                self.stdout.write(msg.format(name=person.name, identifier=identifier.identifier))
