from optparse import make_option
from django.core.management.base import NoArgsCommand
from ...models import Release, Category, Entry, EntryLineItem


class Command(NoArgsCommand):
    help = 'Delete existing declarations of members interests - allows for subsequent re-importing of data.'

    option_list = NoArgsCommand.option_list + (
        make_option(
            '--commit',
            action='store_true',
            dest='commit',
            help='Actually update the database'),)

    def handle_noargs(self, **options):
        count_releases = Release.objects.count()
        count_categories = Category.objects.count()
        count_entries = Entry.objects.count()
        count_entrylineitems = EntryLineItem.objects.count()

        print "  Deleting", count_releases, "releases"
        print "  Deleting", count_categories, "categories"
        print "  Deleting", count_entries, "entries"
        print "  Deleting", count_entrylineitems, "entrylineitems\n"

        if options['commit']:
            print "  Executing the delete"
            Release.objects.all().delete()
            Category.objects.all().delete()
        else:
            print "  Not executing the delete (--commit not specified)"
