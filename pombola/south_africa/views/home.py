from info.models import (
    InfoPage, Category as BlogCategory, Tag as BlogTag
)

from pombola.core.views import HomeView
from pombola.core.models import Person


class SAHomeView(HomeView):

    def get_context_data(self, **kwargs):
        context = super(SAHomeView, self).get_context_data(**kwargs)

        articles = InfoPage.objects.filter(
            kind=InfoPage.KIND_BLOG).order_by("-publication_date")

        articles_for_front_page = \
            InfoPage.objects.filter(
                categories__slug__in=(
                    'week-parliament',
                    'impressions'
                )
            ).order_by('-publication_date')

        context['news_articles'] = articles_for_front_page[:2]

        try:
            context['featured_mp'] = Person.objects.get(slug='gijimani-jim-skosana')
        except Person.DoesNotExist:
            context['featured_mp'] = None

        try:
            context['infographic'] = BlogTag.objects.get(name='infographic'). \
                entries.order_by('-created')[0]
        except BlogTag.DoesNotExist:
            context['infographic'] = None

        return context
