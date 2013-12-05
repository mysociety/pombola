from django.views.generic import DetailView
from django.http import Http404

from .models import Slide

class SlideAfterView(DetailView):

    model = Slide
    template_name = 'spinner/display.html'
    context_object_name = 'slide'

    def get_object(self):
        last_slide_id = self.request.GET.get('id', None)
        last_slide = None

        if last_slide_id:
            try:
                last_slide = Slide.objects.get(pk=last_slide_id)
            except Slide.DoesNotExist:
                print 'not found'
                pass

        print last_slide_id
        print last_slide
        if last_slide:
            print last_slide.id

        next_slide = Slide.objects.slide_after(last_slide)

        if not next_slide:
            raise Http404()

        return next_slide


