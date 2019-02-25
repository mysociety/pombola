import random

from info.models import (
    InfoPage, Category as BlogCategory, Tag as BlogTag
)

from pombola.core.views import HomeView
from pombola.core.models import Person
from pombola.surveys.models import Survey


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

        all_featured_mps = Person.objects.get_featured()

        if len(all_featured_mps) > 0:
            context['featured_mp'] = random.choice(all_featured_mps)
        else:
            context['featured_mp'] = None

        try:
            context['infographic'] = BlogTag.objects.get(name='infographic'). \
                entries.order_by('-created')[0]
        except BlogTag.DoesNotExist:
            context['infographic'] = None

        try:
            context['survey'] = Survey.objects.latest()
        except Survey.DoesNotExist:
            context['survey'] = None

        return context
