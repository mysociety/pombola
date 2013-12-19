# Commented out as unused, but possibly useful in future

# from django.views.generic import DetailView
# from django.http import Http404
#
# from .models import Slide
#
# class SlideAfterView(DetailView):
#
#     model = Slide
#     template_name = 'spinner/display-slide.html'
#     context_object_name = 'slide'
#
#     def get_object(self):
#         last_slide_id = self.request.GET.get('id', None)
#         last_slide = None
#
#         # If we were given an id try to load it
#         if last_slide_id:
#             try:
#                 last_slide = Slide.objects.get(pk=last_slide_id)
#             except Slide.DoesNotExist:
#                 pass
#
#         # Get the next slide
#         next_slide = Slide.objects.slide_after(last_slide)
#
#         # 404 if there is no next slide (which means that there are no active
#         # slides)
#         if not next_slide:
#             raise Http404()
#
#         return next_slide
#
#
