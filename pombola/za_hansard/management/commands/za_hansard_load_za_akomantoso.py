from speeches.management.import_commands import ImportCommand
from za_hansard.importers.import_za_akomantoso import ImportZAAkomaNtoso

class Command(ImportCommand):
    importer_class = ImportZAAkomaNtoso
    document_extension = 'xml'
