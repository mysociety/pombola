from haystack.backends.elasticsearch_backend import (
    ElasticsearchSearchBackend,
    ElasticsearchSearchEngine,
    )


class ZAElasticBackend(ElasticsearchSearchBackend):
    def __init__(self, connection_alias, **connection_options):
        super(ZAElasticBackend, self).__init__(
            connection_alias, **connection_options)

        analyzers = self.DEFAULT_SETTINGS['settings']['analysis']['analyzer']
        analyzers['folding'] = {
            "tokenizer": "standard",
            "filter": ["lowercase", "asciifolding"],
            }

    def build_schema(self, fields):
        content_field_name, mapping = super(ZAElasticBackend, self).build_schema(fields)

        # Change all the mappings that were 'snowball' to 'folding'
        for field_name, field_class in fields.items():
            field_mapping = mapping[field_class.index_fieldname]

            if field_mapping['type'] == 'string' and field_class.indexed:
                if not hasattr(field_class, 'facet_for') and \
                        not field_class.field_type in('ngram', 'edge_ngram'):
                    field_mapping["analyzer"] = "folding"

            mapping.update({field_class.index_fieldname: field_mapping})

        return (content_field_name, mapping)


class ZAElasticSearchEngine(ElasticsearchSearchEngine):
    """Subclass to use the new subclassed backend"""
    backend = ZAElasticBackend
