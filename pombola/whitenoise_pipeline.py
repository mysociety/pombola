# Suggestion from: https://github.com/mozilla/playdoh/issues/173
from pipeline.storage import PipelineMixin
from whitenoise.django import GzipManifestStaticFilesStorage

class GzipManifestPipelineStorage(PipelineMixin, GzipManifestStaticFilesStorage):
    pass
