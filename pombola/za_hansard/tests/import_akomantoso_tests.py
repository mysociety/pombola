# -*- coding: utf-8 -*-

import os

from django.core.management import call_command
from django.utils.unittest import skip

from instances.tests import InstanceTestCase
from popolo_name_resolver.resolve import EntityName, recreate_entities

from speeches.models import Speaker
from za_hansard.importers.import_za_akomantoso import ImportZAAkomaNtoso, title_case_heading

import logging
logging.disable(logging.WARNING)


class ImportZAAkomaNtosoTests(InstanceTestCase):

    @classmethod
    def setUpClass(cls):
        cls._in_fixtures = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test_inputs', 'hansard')
        super(ImportZAAkomaNtosoTests, cls).setUpClass()
        call_command('update_index', interactive=False, verbosity=0)
        recreate_entities()

    @skip("Depends on external API data")
    def test_import(self):
        return
        document_path = os.path.join(self._in_fixtures, 'NA200912.xml')

        an = ImportZAAkomaNtoso(instance=self.instance, commit=True)
        section = an.import_document(document_path)

        self.assertTrue(section is not None)

        # Check that all the sections have correct looking titles
        for sub in section.children.all():
            self.assertFalse("Member'S" in sub.title)

        speakers = Speaker.objects.all()
        resolved = filter(lambda s: s.person != None, speakers)
        THRESHOLD = 48

        logging.info(
                "%d above threshold %d/%d?"
                % (len(resolved), THRESHOLD, len(speakers)))

        self.assertTrue(
                len(resolved) >= THRESHOLD,
                "%d above threshold %d/%d"
                % (len(resolved), THRESHOLD, len(speakers)))

    def test_title_casing(self):
        tests = (
            # initial, expected
            ("ALL CAPS", "All Caps"),
            ("MEMBER'S Statement", "Member's Statement"),
            ("member’s", "Member’s"),
        )

        for initial, expected in tests:
            self.assertEqual(title_case_heading(initial), expected)
