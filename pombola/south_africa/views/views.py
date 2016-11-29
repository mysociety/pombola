import warnings

from django.utils.translation import ugettext_lazy as _

from info.views import InfoBlogView
from info.views import InfoPageView

from pombola.core.views import CommentArchiveMixin


class SANewsletterPage(InfoPageView):
    template_name = 'south_africa/info_newsletter.html'


class SAInfoBlogView(CommentArchiveMixin, InfoBlogView):
    pass
