from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, DetailView
from hansard.models import Sitting

# import models
# from django.shortcuts  import render_to_response, redirect
# from django.template   import RequestContext
# 
# 
# def default(request):
#     return render_to_response(
#         'hansard/default.html',
#         {
#             'chunks': models.Chunk.objects.all(),
#         },
#         context_instance=RequestContext(request)
#     )
# 
# #   /hansard/venue/yyyy/mm/dd/hh:mm
# 

"""
Hansard views - possible url structure:

The url to the various hansard pages follow this sort of structure:

  ../venue/yyyy/mm/dd/day_id-slug-that-can-be-ignored

'venue' is the slug of the debating chamber, committee etc that the report is
for.

'yyyy', 'mm', 'dd', 'hh:mm' is the date down to the start of the sitting. It is
assumed that one chamber can only do one thing at a time so there will never be
a conflict.

    ^
    ^(?P<venue>[\w\-]+)/
    ^(?P<venue>[\w\-]+)/(?P<year>\d{4})/
    ^(?P<venue>[\w\-]+)/(?P<year>\d{4})/(?P<month>\d{2})/
    ^(?P<venue>[\w\-]+)/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>)/
    ^(?P<venue>[\w\-]+)/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>)/(?P<day_id>\d+)-(?P<slug>[\w\-]+)

"""

class IndexView(TemplateView):
    template_name = "hansard/index.html"

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)

        context['sittings'] = Sitting.objects.all() # FIXME - put a limit on here [0:10]

        return context


class SittingView(DetailView):
    model = Sitting


# class BaseView ( View ):
#     pass
# 
# class VenueMixin( object ):
# 
#     def get_venue(self): 
#         "Return the venue that should be searched for. 404s if not found." 
#         return get_object_or_404( Venue, slug=self.kwargs['slug'] )
# 
# class IndexView( BaseView ):
#     pass
# 
# class VenueView( VenueMixin, BaseView ):
#     pass
# 
# class YearView( YearMixin, VenueView ):
#     pass
# 
