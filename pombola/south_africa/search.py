from haystack.backends.elasticsearch_backend import (
    ElasticsearchSearchBackend,
    ElasticsearchSearchEngine,
    )


class ZAElasticBackend(ElasticsearchSearchBackend):
    def __init__(self, connection_alias, **connection_options):
        super(ZAElasticBackend, self).__init__(connection_alias, **connection_options)

        self.DEFAULT_SETTINGS['settings']['analysis']['analyzer']['default'] = {
            "tokenizer": "standard",
            "filter": ["lowercase", "asciifolding"],
            }


class ZAElasticSearchEngine(ElasticsearchSearchEngine):
    """Subclass to use the new subclassed backend"""
    backend = ZAElasticBackend
