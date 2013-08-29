from django.views.generic import DetailView
from models import InfoPage

class InfoPageView(DetailView):
    """Show the page for the given slug"""
    model = InfoPage
    queryset = InfoPage.objects.filter(kind=InfoPage.KIND_PAGE)
