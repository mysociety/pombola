import csv
from optparse import make_option
from os.path import join, dirname

from django.core.management.base import BaseCommand

from mapit.models import Type, Name, NameType

corrections_filename = join(
    dirname(__file__), '..', '..', 'data', 'lga-name-corrections.csv'
)

class Command(BaseCommand):

    help = "Add alternative names for LGA areas to MapIt Names"

    option_list = BaseCommand.option_list + (
        make_option(
            '--replace',
            action='store_true',
            default=False,
            help="If there's an existing Name for an area, replace it"
        ),
        make_option(
            '--commit',
            action='store_true',
            default=False,
            help="Actually make changes to the database",
        ),
    )

    def handle(self, *args, **options):
        with open(corrections_filename, 'rb') as f:
            reader = csv.DictReader(f)
            all_rows = [row for row in reader]
        # First check that all state names can be found:
        all_states_found = True
        state_name_to_mapit_area = {}
        state_type = Type.objects.get(code='STA')
        for row in all_rows:
            atlas_state_name = row['Atlas State']
            try:
                mapit_state = state_type.areas.get(
                    name__iexact=atlas_state_name
                )
                state_name_to_mapit_area[atlas_state_name] = mapit_state
            except Exception as e:
                all_states_found = False
                print u"Error trying to find {0}: {1}".format(
                    atlas_state_name, unicode(e)
                )
                continue
        if not all_states_found:
            return
        # Now go through each addition, and see if there's already a
        # polling unit name for that:
        pu_name_type = NameType.objects.get(code='poll_unit')
        lga_type = Type.objects.get(code='LGA')
        for row in all_rows:
            lga_area = lga_type.areas.get(id=row['MapIt Area ID'])
            atlas_state_name = row['Atlas State']
            state_area = state_name_to_mapit_area[atlas_state_name]
            if lga_area.parent_area != state_area:
                msg = "Mismatch between atlas state ({atlas_state}) and LGA parent state from MapIt ({lga_parent_state})"
                raise msg.format(
                    atlas_state=state_area,
                    lga_parent_state=lga_area.parent_area
                )
            new_name = row['Atlas LGA Name']
            add_name = True
            try:
                existing_name = pu_name_type.names.get(area=lga_area)
                if new_name == existing_name.name:
                    add_name = False
                    print "'{area}' already had the correct name ('{existing_name}')".format(
                        area=lga_area, existing_name=existing_name.name
                    )
                else:
                    print "'{area}' already had a name ('{existing_name}')".format(
                        area=lga_area, existing_name=existing_name.name
                    ),
                    if options['replace']:
                        if options['commit']:
                            msg = "- deleting it to replace it with '{new_name}'"
                            print msg.format(new_name=new_name)
                            existing_name.delete()
                        else:
                            msg = "- would delete it, to replace with '{new_name}', but --commit wasn't specified"
                            print msg.format(new_name=new_name)
                    else:
                        add_name = False
                        print "- not replacing it since --replace wasn't specified"
            except Name.DoesNotExist:
                pass
            if add_name:
                if options['commit']:
                    print "Adding the new name ('{new_name}') for area '{area}'".format(
                        new_name=new_name, area=lga_area
                    )
                    pu_name_type.names.create(area=lga_area, name=new_name)
                else:
                    msg = "Would add the new name '{new_name}' for area '{area}', but --commit wasn't specified"
                    print msg.format(new_name=new_name, area=lga_area)
