from info.views import InfoBlogView, InfoPageView

from pombola.core.views import CommentArchiveMixin


class SANewsletterPage(InfoPageView):
    template_name = 'south_africa/info_newsletter.html'


class SAInfoBlogView(CommentArchiveMixin, InfoBlogView):
    pass
