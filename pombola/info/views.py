from datetime import date

from django.views.generic import DetailView, ListView
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse_lazy
from django.db.models import F
from django.shortcuts import get_list_or_404
from django.conf import settings

from models import InfoPage, Category, Tag, ViewCount


class BlogMixin(object):

    def get_context_data(self, **kwargs):
        context = super(BlogMixin, self).get_context_data(**kwargs)

        context['all_categories'] = Category.objects.all().order_by('name')

        context['recent_posts'] = InfoPage.objects \
            .filter(kind=InfoPage.KIND_BLOG) \
            .order_by("-publication_date")

        return context


class InfoBlogList(BlogMixin, ListView):
    """Show list of blog posts"""
    model = InfoPage
    queryset = InfoPage.objects.filter(kind=InfoPage.KIND_BLOG).order_by("-publication_date")
    paginate_by = settings.INFO_POSTS_PER_LIST_PAGE
    template_name = 'info/blog_list.html'


class InfoBlogLabelBase(InfoBlogList):

    def get_queryset(self):
        slugs = self.kwargs['slug'].split(',')
        queryset = super(InfoBlogLabelBase, self).get_queryset()
        filter_args = { self.filter_field: slugs }
        return queryset.filter(**filter_args)

    def get_context_data(self, **kwargs):
        context = super(InfoBlogLabelBase, self).get_context_data(**kwargs)

        slugs = self.kwargs['slug'].split(',')
        context[self.context_key] = get_list_or_404(self.context_filter_model, slug__in=slugs)

        return context


class InfoBlogCategory(InfoBlogLabelBase):
    context_key  = 'categories'
    context_filter_model = Category
    filter_field = 'categories__slug__in'

    def get_context_data(self, **kwargs):
        context = super(InfoBlogCategory, self).get_context_data(**kwargs)

        # Filter the recent posts to be specific to this category
        slugs = self.kwargs['slug'].split(',')
        context['recent_posts'] = context['recent_posts'].filter(categories__slug__in=slugs)

        context['category_names'] = []
        for category in context['categories']:
            context['category_names'].append(category.name)

        return context


class InfoBlogTag(InfoBlogLabelBase):
    context_key  = 'tags'
    context_filter_model = Tag
    filter_field = 'tags__slug__in'


class InfoBlogView(BlogMixin, DetailView):
    """Show the blog post for the given slug"""
    model = InfoPage
    queryset = InfoPage.objects.filter(kind=InfoPage.KIND_BLOG)
    template_name = 'info/blog_post.html'

    def get(self, request, *args, **kwargs):
        response = super(InfoBlogView, self).get(request, *args, **kwargs)

        _, created = ViewCount.objects.get_or_create(
            page=self.object,
            date=date.today(),
            defaults={'count': 1},
            )

        if not created:
            (ViewCount.objects.filter(page=self.object, date=date.today())
             .update(count=F('count')+1))

        return response


class InfoBlogFeed(Feed):
    """Create a feed with the latest 10 blog entries in"""
    title = "Recent blog posts"
    link = reverse_lazy('info_blog_list')
    description = "Recent blog posts"

    def items(self):
        return InfoPage.objects.filter(kind=InfoPage.KIND_BLOG).order_by("-publication_date")[:10]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.content_as_cleaned_html


class InfoPageView(DetailView):
    """Show the page for the given slug"""
    model = InfoPage
    queryset = InfoPage.objects.filter(kind=InfoPage.KIND_PAGE)
