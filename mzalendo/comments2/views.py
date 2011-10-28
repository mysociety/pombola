import urllib
import textwrap

from django import http
from django.conf import settings
from django.contrib import comments
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core import urlresolvers
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.shortcuts import render_to_response
from django.template   import RequestContext
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.html import escape
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic.list_detail import object_detail, object_list

from comments2.forms import CommentForm

def get_object(module_name, slug):
    # retrieve the content_type that we need
    ct = get_object_or_404( ContentType, model=module_name )

    # retrieve the object
    obj = get_object_or_404( ct.model_class(), slug=slug )

    return obj
    

def list_for(request, module_name, slug):
    """Display comments"""

    obj = get_object( module_name, slug )

    return render_to_response(
        'comments/list_for.html',
        {
            'object': obj,
        },
        context_instance=RequestContext(request)
    )



@login_required
@csrf_protect
def add(request, module_name, slug):

    obj = get_object( module_name, slug )
    comment = False

    if request.method == 'POST':
        form = CommentForm(obj, request.POST)
        if form.is_valid():
            comment = form.get_comment_object()
            comment.ip_address = request.META['REMOTE_ADDR']
            comment.user = request.user
            comment.save()
            
    else:
        form = CommentForm(obj)
    
    

    return render_to_response(
        'comments/add.html',
        {
            'object': obj,
            'form':   form,
            'comment': comment,
        },
        context_instance=RequestContext(request)
    )




class CommentPostBadRequest(http.HttpResponseBadRequest):
    """
    Response returned when a comment post is invalid. If ``DEBUG`` is on a
    nice-ish error message will be displayed (for debugging purposes), but in
    production mode a simple opaque 400 page will be displayed.
    """
    def __init__(self, why):
        super(CommentPostBadRequest, self).__init__()
        if settings.DEBUG:
            self.content = render_to_string("comments/400-debug.html", {"why": why})

# @csrf_protect
# @require_POST
# def post_comment(request, next=None, using=None):
#     """
#     Post a comment.
# 
#     HTTP POST is required. If ``POST['submit'] == "preview"`` or if there are
#     errors a preview template, ``comments/preview.html``, will be rendered.
#     """
#     # Fill out some initial data fields from an authenticated user, if present
#     data = request.POST.copy()
#     if request.user.is_authenticated():
#         if not data.get('name', ''):
#             data["name"] = request.user.get_full_name() or request.user.username
#         if not data.get('email', ''):
#             data["email"] = request.user.email
# 
#     # Check to see if the POST data overrides the view's next argument.
#     next = data.get("next", next)
# 
#     # Look up the object we're trying to comment about
#     ctype = data.get("content_type")
#     object_pk = data.get("object_pk")
#     if ctype is None or object_pk is None:
#         return CommentPostBadRequest("Missing content_type or object_pk field.")
#     try:
#         model = models.get_model(*ctype.split(".", 1))
#         target = model._default_manager.using(using).get(pk=object_pk)
#     except TypeError:
#         return CommentPostBadRequest(
#             "Invalid content_type value: %r" % escape(ctype))
#     except AttributeError:
#         return CommentPostBadRequest(
#             "The given content-type %r does not resolve to a valid model." % \
#                 escape(ctype))
#     except ObjectDoesNotExist:
#         return CommentPostBadRequest(
#             "No object matching content-type %r and object PK %r exists." % \
#                 (escape(ctype), escape(object_pk)))
#     except (ValueError, ValidationError), e:
#         return CommentPostBadRequest(
#             "Attempting go get content-type %r and object PK %r exists raised %s" % \
#                 (escape(ctype), escape(object_pk), e.__class__.__name__))
# 
#     # Do we want to preview the comment?
#     preview = "preview" in data
# 
#     # Construct the comment form
#     form = comments.get_form()(target, data=data)
# 
#     # Check security information
#     if form.security_errors():
#         return CommentPostBadRequest(
#             "The comment form failed security verification: %s" % \
#                 escape(str(form.security_errors())))
# 
#     # If there are errors or if we requested a preview show the comment
#     if form.errors or preview:
#         template_list = [
#             # These first two exist for purely historical reasons.
#             # Django v1.0 and v1.1 allowed the underscore format for
#             # preview templates, so we have to preserve that format.
#             "comments/%s_%s_preview.html" % (model._meta.app_label, model._meta.module_name),
#             "comments/%s_preview.html" % model._meta.app_label,
#             # Now the usual directory based template heirarchy.
#             "comments/%s/%s/preview.html" % (model._meta.app_label, model._meta.module_name),
#             "comments/%s/preview.html" % model._meta.app_label,
#             "comments/preview.html",
#         ]
#         return render_to_response(
#             template_list, {
#                 "comment" : form.data.get("comment", ""),
#                 "form" : form,
#                 "next": next,
#             },
#             RequestContext(request, {})
#         )
# 
#     # Otherwise create the comment
#     comment = form.get_comment_object()
#     comment.ip_address = request.META.get("REMOTE_ADDR", None)
#     if request.user.is_authenticated():
#         comment.user = request.user
# 
#     # Signal that the comment is about to be saved
#     responses = signals.comment_will_be_posted.send(
#         sender  = comment.__class__,
#         comment = comment,
#         request = request
#     )
# 
#     for (receiver, response) in responses:
#         if response == False:
#             return CommentPostBadRequest(
#                 "comment_will_be_posted receiver %r killed the comment" % receiver.__name__)
# 
#     # Save the comment and signal that it was saved
#     comment.save()
#     signals.comment_was_posted.send(
#         sender  = comment.__class__,
#         comment = comment,
#         request = request
#     )
# 
#     return next_redirect(data, next, comment_done, c=comment._get_pk_val())


# def next_redirect(data, default, default_view, **get_kwargs):
#     """
#     Handle the "where should I go next?" part of comment views.
# 
#     The next value could be a kwarg to the function (``default``), or a
#     ``?next=...`` GET arg, or the URL of a given view (``default_view``). See
#     the view modules for examples.
# 
#     Returns an ``HttpResponseRedirect``.
#     """
#     next = data.get("next", default)
#     if next is None:
#         next = urlresolvers.reverse(default_view)
#     if get_kwargs:
#         if '#' in next:
#             tmp = next.rsplit('#', 1)
#             next = tmp[0]
#             anchor = '#' + tmp[1]
#         else:
#             anchor = ''
# 
#         joiner = ('?' in next) and '&' or '?'
#         next += joiner + urllib.urlencode(get_kwargs) + anchor
#     return HttpResponseRedirect(next)
# 
# def confirmation_view(template, doc="Display a confirmation view."):
#     """
#     Confirmation view generator for the "comment was
#     posted/flagged/deleted/approved" views.
#     """
#     def confirmed(request):
#         comment = None
#         if 'c' in request.GET:
#             try:
#                 comment = comments.get_model().objects.get(pk=request.GET['c'])
#             except (ObjectDoesNotExist, ValueError):
#                 pass
#         return render_to_response(template,
#             {'comment': comment},
#             context_instance=RequestContext(request)
#         )
# 
#     confirmed.__doc__ = textwrap.dedent("""\
#         %s
# 
#         Templates: `%s``
#         Context:
#             comment
#                 The posted comment
#         """ % (doc, template)
#     )
#     return confirmed
# 
# comment_done = confirmation_view(
#     template = "comments/posted.html",
#     doc = """Display a "comment was posted" success page."""
# )
# 
