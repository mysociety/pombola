from django.views.generic import DetailView, ListView
from models import InfoPage

class InfoBlogList(ListView):
    """Show list of blog posts"""
    model = InfoPage
    queryset = InfoPage.objects.filter(kind=InfoPage.KIND_BLOG).order_by("-publication_date")
    paginate_by = 10
    template_name = 'info/blog_list.html'

class InfoBlogView(DetailView):
    """Show the blog post for the given slug"""
    model = InfoPage
    queryset = InfoPage.objects.filter(kind=InfoPage.KIND_BLOG)
    template_name = 'info/blog_post.html'


class InfoPageView(DetailView):
    """Show the page for the given slug"""
    model = InfoPage
    queryset = InfoPage.objects.filter(kind=InfoPage.KIND_PAGE)


