import sys

from django.core.management.base import BaseCommand

from haystack import connections as haystack_connections
from haystack.exceptions import NotHandled
from haystack.query import SearchQuerySet
from haystack.utils.app_loading import get_models, load_apps


def get_all_indexed_models():

    backends = haystack_connections.connections_info.keys()

    available_models = {}

    for backend_key in backends:
        unified_index = haystack_connections[backend_key].get_unified_index()
        for app in load_apps():
            for model in get_models(app):
                try:
                    unified_index.get_index(model)
                except NotHandled:
                    continue
                model_name = model.__module__ + '.' + model.__name__
                available_models[model_name] = {
                    'backend_key': backend_key,
                    'app': app,
                    'model': model,
                }

    return available_models

def get_models_to_check(model_names, available_models):

    models_to_check = []

    if model_names:
        missing_models = False
        for model_name in model_names:
            if model_name in available_models:
                models_to_check.append(model_name)
            else:
                missing_models = True
                print "There was no model {0} with a search index".format(model_name)
            if missing_models:
                print "Some models were not found; they must be one of:"
                for model in sorted(available_models.keys()):
                    print " ", model
                sys.exit(1)
    else:
        models_to_check = sorted(available_models.keys())

    return models_to_check


class Command(BaseCommand):
    args = 'MODEL ...'
    help = 'Get all search results for the given models'

    def handle(self, *args, **options):

        available_models = get_all_indexed_models()

        models_to_check = get_models_to_check(args, available_models)

        # Now we know which models to check, do that:

        for model_name in models_to_check:
            model_details = available_models[model_name]

            backend_key = model_details['backend_key']
            model = model_details['model']

            backend = haystack_connections[backend_key].get_backend()
            unified_index = haystack_connections[backend_key].get_unified_index()

            index = unified_index.get_index(model)

            qs = index.build_queryset()
            print "Checking {0} ({1} objects in the database)".format(
                model_name, qs.count()
            )
            # Get all the primary keys from the database:
            pks_in_database = set(
                unicode(pk) for pk in qs.values_list('pk', flat=True)
            )
            # Then go through every search result for that
            # model, and check that the primary key is one
            # that's in the database:
            for search_result in SearchQuerySet(using=backend.connection_alias).models(model):
                if search_result.pk not in pks_in_database:
                    print "      stale search entry for primary key", search_result.pk
