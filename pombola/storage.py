import glob
import os

from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import CachedStaticFilesStorage

from pipeline.storage import PipelineMixin


class ImageSpriteMixin(object):
    sprite_dirs = 'images/sprites/'

    def post_process(self, paths, dry_run=False, **options):
        if dry_run:
            return

        for image_dir in finders.find(self.sprite_dirs, all=True):
            for png in glob.glob(image_dir + '/*.png'):
                filename = os.path.basename(png)
                with open(png) as source:
                    self.save(self.sprite_dirs + filename, source)

        super_class = super(ImageSpriteMixin, self)
        if hasattr(super_class, 'post_process'):
            for name, hashed_name, processed in super_class.post_process(paths.copy(), dry_run, **options):
                yield name, hashed_name, processed


class PipelineCachedStorage(PipelineMixin, ImageSpriteMixin, CachedStaticFilesStorage):
    pass
