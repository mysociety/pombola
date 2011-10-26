import models
from django.shortcuts  import render_to_response, redirect
from django.template   import RequestContext


def default(request):
    return render_to_response(
        'hansard/default.html',
        {
            'chunks': models.Chunk.objects.all(),
        },
        context_instance=RequestContext(request)
    )

