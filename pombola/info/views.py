from django.views.generic import DetailView
from models import InfoPage

class InfoPageView(DetailView):
    """Show the page, or 'index' if no slug"""
    model = InfoPage
