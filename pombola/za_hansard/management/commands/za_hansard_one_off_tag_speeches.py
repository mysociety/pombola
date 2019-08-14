# This is a noe-off script to tag all speeches that are under certain top-level
# categories with a certain tag. This tagging should be done when the speeches
# are scraped, and this script is to update speeches created before the code
# changes to add the tagging.


import sys

from speeches.models import Section, Tag

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Restructure the hansard section hierarchy'

    mapping = (
        # Section heading, tag name
        ('Hansard', 'hansard'),
        ('Committee Minutes', 'committee'),
        ('Questions', 'question'),
    )

    indent_depth = 0


    def handle(self, *args, **options):
        for section_heading, tag_name in self.mapping:

            # Get the top level section with the matching name
            try:
                section = Section.objects.get(heading=section_heading, parent=None)
            except Section.DoesNotExist:
                sys.stderr.write("Can't find top level section '%s'\n" % section_heading )
                continue

            # Get or create the tag
            tag, tag_created = Tag.objects.get_or_create(name=tag_name, instance=section.instance)

            # Tag the speeches
            self.tag_speeches_under(section, tag)


    def tag_speeches_under(self, section, tag):
        """
        Tag all speeches in this section, then recurse into child sections.
        """

        # Poor man's pretty printing :)
        indent = " " * self.indent_depth

        print indent + "looking at %s" % section

        # tag all speeches
        for speech in section.speech_set.all():
            print indent + "  " + "Tagging '%s' with '%s" % (speech, tag)
            speech.tags.add(tag)

        # descend into subsections
        for child_section in section.children.all():
            self.indent_depth += 2
            self.tag_speeches_under(child_section, tag)
            self.indent_depth -= 2


